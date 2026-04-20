import logging
import time

from pydoover.docker import Application

from .app_config import IQFlowWindSensorConfig
from .app_tags import IQFlowWindSensorTags
from .app_ui import IQFlowWindSensorUI
from .gust_tracker import RollingMax
from .iqws_driver import (
    IQWSReading,
    IQWSVariant,
    REG_BAUD,
    REG_PARITY,
    REG_SLAVE_ID,
    REG_WIND_SPEED,
    WindUnit,
    convert_speed,
    decode,
    encode_baud,
    encode_parity,
    num_registers_for,
    validate_slave_id,
)

log = logging.getLogger(__name__)

MODBUS_HOLDING_REGISTER = 3

SIM_TAG_SPEED_RAW = "sim_wind_speed_raw"
SIM_TAG_DIRECTION_RAW = "sim_wind_direction_raw"


class IQFlowWindSensorApplication(Application):
    config_cls = IQFlowWindSensorConfig
    tags_cls = IQFlowWindSensorTags
    ui_cls = IQFlowWindSensorUI

    config: IQFlowWindSensorConfig
    tags: IQFlowWindSensorTags

    # The main loop fires every second; we throttle the actual Modbus poll
    # to `config.poll_interval_seconds` ourselves so that gust bookkeeping
    # and command-tag handling stay responsive between polls.
    loop_target_period = 1

    async def setup(self):
        self._gust = RollingMax(self.config.gust_window_seconds.value)
        self._last_poll_ts: float = 0.0
        self._last_successful_read_ts: float = 0.0
        self._last_gust_window = self.config.gust_window_seconds.value

    async def main_loop(self):
        now = time.time()

        # Keep the gust window in sync with live config edits.
        window = self.config.gust_window_seconds.value
        if window != self._last_gust_window:
            self._gust.set_window(window)
            self._last_gust_window = window

        await self._handle_command_tags()

        if now - self._last_poll_ts >= self.config.poll_interval_seconds.value:
            self._last_poll_ts = now
            await self._poll(now)

    # -----------------------------------------------------------------
    # Polling
    # -----------------------------------------------------------------

    async def _poll(self, now: float) -> None:
        variant = self._variant()
        registers = await self._read_registers(variant)
        reading = decode(registers, variant)
        await self._publish(reading, now)

    async def _read_registers(self, variant: IQWSVariant):
        if self._sim_enabled():
            return self._read_from_sim(variant)

        try:
            return await self.modbus_iface.read_registers(
                bus_id=self.config.modbus_config.name.value,
                modbus_id=self.config.slave_id.value,
                start_address=REG_WIND_SPEED,
                num_registers=num_registers_for(variant),
                register_type=MODBUS_HOLDING_REGISTER,
            )
        except Exception:
            log.exception("Modbus read failed")
            return None

    def _read_from_sim(self, variant: IQWSVariant):
        sim_key = self.config.sim_app_key.value
        raw_speed = self.get_tag(SIM_TAG_SPEED_RAW, sim_key)
        if raw_speed is None:
            return None
        values = [int(raw_speed)]
        if variant is IQWSVariant.COMBINED:
            raw_dir = self.get_tag(SIM_TAG_DIRECTION_RAW, sim_key)
            if raw_dir is None:
                return None
            values.append(int(raw_dir))
        return values

    def _sim_enabled(self) -> bool:
        return bool(self.config.sim_app_key.value)

    def _variant(self) -> IQWSVariant:
        return IQWSVariant(self.config.variant.value)

    # -----------------------------------------------------------------
    # Publishing
    # -----------------------------------------------------------------

    async def _publish(self, reading: IQWSReading, now: float) -> None:
        unit = WindUnit(self.config.display_unit.value)
        speed_in_unit = convert_speed(reading.speed_mps, unit)

        read_ok = reading.speed_mps is not None and (
            self._variant() is IQWSVariant.SPEED_ONLY
            or reading.direction_index is not None
        )

        if read_ok:
            self._last_successful_read_ts = now
            self._gust.add(speed_in_unit, now)
            await self.tags.wind_speed.set(round(speed_in_unit, 2))
            gust = self._gust.current(now)
            if gust is not None:
                await self.tags.wind_gust.set(round(gust, 2))
            if reading.direction_degrees is not None:
                await self.tags.wind_direction_degrees.set(reading.direction_degrees)
            if reading.direction_compass is not None:
                await self.tags.wind_direction_compass.set(reading.direction_compass)
            if reading.raw_speed is not None:
                await self.tags.raw_speed_value.set(reading.raw_speed)
            if reading.raw_direction is not None:
                await self.tags.raw_direction_index.set(reading.raw_direction)
            await self.tags.last_read_time.set(now)
            await self.tags.comms_ok.set(True)
            return

        # No valid reading this cycle.
        staleness = now - self._last_successful_read_ts
        timeout = self.config.no_comms_timeout_seconds.value
        if self._last_successful_read_ts == 0 or staleness > timeout:
            await self.tags.comms_ok.set(False)
            # Let the gust window drain naturally rather than zeroing the tag.
            gust = self._gust.current(now)
            if gust is None:
                await self.tags.wind_gust.set(0)

    # -----------------------------------------------------------------
    # Technician command tags
    # -----------------------------------------------------------------

    async def _handle_command_tags(self) -> None:
        if self._sim_enabled():
            # No real Modbus bus in sim mode — refuse writes loudly so
            # technicians don't think they reconfigured a real sensor.
            for tag_name in ("cmd_set_slave_id", "cmd_set_baud", "cmd_set_parity"):
                if self.tags.get(tag_name).get() is not None:
                    await self._finalise_cmd(tag_name, "error: simulator mode, write ignored")
            return

        slave_cmd = self.tags.cmd_set_slave_id.get()
        if slave_cmd is not None:
            await self._write_commissioning(
                "cmd_set_slave_id",
                REG_SLAVE_ID,
                encode_fn=validate_slave_id,
                value=slave_cmd,
            )

        baud_cmd = self.tags.cmd_set_baud.get()
        if baud_cmd is not None:
            await self._write_commissioning(
                "cmd_set_baud",
                REG_BAUD,
                encode_fn=encode_baud,
                value=baud_cmd,
            )

        parity_cmd = self.tags.cmd_set_parity.get()
        if parity_cmd is not None:
            await self._write_commissioning(
                "cmd_set_parity",
                REG_PARITY,
                encode_fn=encode_parity,
                value=parity_cmd,
            )

    async def _write_commissioning(self, tag_name: str, register: int, *, encode_fn, value) -> None:
        try:
            encoded = encode_fn(value)
        except ValueError as exc:
            await self._finalise_cmd(tag_name, f"error: {exc}")
            return

        try:
            await self.modbus_iface.write_registers(
                bus_id=self.config.modbus_config.name.value,
                modbus_id=self.config.slave_id.value,
                start_address=register,
                values=[encoded],
                register_type=MODBUS_HOLDING_REGISTER,
            )
        except Exception as exc:
            log.exception("Modbus write failed for %s", tag_name)
            await self._finalise_cmd(tag_name, f"error: {exc}")
            return

        await self._finalise_cmd(
            tag_name,
            f"ok: wrote {encoded} to register 0x{register:04X} (power-cycle sensor to apply)",
        )

    async def _finalise_cmd(self, tag_name: str, result: str) -> None:
        await self.tags.last_cmd_result.set(result)
        await self.tags.get(tag_name).set(None)
        log.info("Command %s → %s", tag_name, result)
