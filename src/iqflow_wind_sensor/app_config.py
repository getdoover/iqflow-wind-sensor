from pathlib import Path

from pydoover import config
from pydoover.docker.modbus import ModbusConfig


class IQFlowWindSensorConfig(config.Schema):
    variant = config.Enum(
        "Sensor Variant",
        name="variant",
        choices=["combined", "speed_only"],
        default="combined",
        description="combined = IQWS-D / SD-A (wind speed + direction). "
                    "speed_only = IQWS-S (wind speed only).",
    )

    # Default display name "Modbus Config" sanitizes to the JSON key "modbus_config".
    modbus_config = ModbusConfig()

    slave_id = config.Integer(
        "Slave ID",
        name="slave_id",
        default=1,
        description="Modbus unit / slave ID of the IQWS sensor (1..247).",
    )

    poll_interval_seconds = config.Integer(
        "Poll Interval (seconds)",
        name="poll_interval_seconds",
        default=3,
        description="How often to read the sensor.",
    )

    display_unit = config.Enum(
        "Wind Speed Unit",
        name="display_unit",
        choices=["kmh", "mps", "knots"],
        default="kmh",
        description="Unit used for wind speed and gust tags/UI.",
    )

    gust_window_seconds = config.Integer(
        "Gust Window (seconds)",
        name="gust_window_seconds",
        default=180,
        description="Rolling-window size used to compute the gust (peak) wind speed.",
    )

    no_comms_timeout_seconds = config.Integer(
        "No-Comms Timeout (seconds)",
        name="no_comms_timeout_seconds",
        default=30,
        description="Clear comms_ok after this many seconds without a successful read.",
    )

    sim_app_key = config.Application(
        "Simulator App Key",
        name="sim_app_key",
        default="",
        description="Optional. If set, read wind data from this simulator app's tags "
                    "instead of the Modbus bus. Leave blank for normal operation.",
    )


def export():
    IQFlowWindSensorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "iqflow_wind_sensor",
    )


if __name__ == "__main__":
    export()
