# IQFlow IQWS Wind Sensor

**Doover device driver for the IQFlow IQWS wind speed and direction sensor over Modbus RTU.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

[Getting Started](#getting-started) • [Configuration](#configuration) • [Tags](#tags) • [Hardware](#hardware) • [Developer](DEVELOPMENT.md)

## Overview

Reads wind speed and direction from an [IQFlow IQWS](https://iqflow.io/products/iqws-wind-speed-direction-sensor) sensor (or the equivalent Hunan Firstrate OEM) and publishes them as Doover tags. Supports both the combined speed+direction variant (IQWS-D / IQWS-SD-A) and the speed-only variant (IQWS-S).

The app talks to the sensor through pydoover's `ModbusInterface`, which means it shares the physical RS-485 bus with other Doover apps on the same gateway — it does not open the serial port directly.

## Getting Started

1. Wire the sensor to the gateway's RS-485 port (see [Hardware](#hardware)).
2. Install this app onto the target device via the Doover platform.
3. Set at minimum the `Sensor Variant`, `Slave ID`, and the serial port fields inside `Modbus Bus`. Defaults match the sensor's factory config (9600 8N1, slave ID 1).
4. Watch the `wind_speed`, `wind_gust`, and `wind_direction_*` tags populate.

### Local testing

```bash
uv sync
uv run pytest tests -v
doover app run
```

`doover app run` brings up the bundled simulator via docker-compose. With `sim_app_key` set (as in `simulators/app_config.json`), the app reads wind data from the simulator's tags instead of the Modbus bus, so no hardware is required.

## Configuration

Fields are declared in [`src/iqflow_wind_sensor/app_config.py`](src/iqflow_wind_sensor/app_config.py). Run `uv run export-config && uv run export-ui` after any change to regenerate `doover_config.json`.

| Setting | Description | Default |
|---|---|---|
| **Sensor Name** | Display name shown in the UI. | `Wind Sensor` |
| **Sensor Variant** | `combined` (IQWS-D / SD-A) or `speed_only` (IQWS-S). | `combined` |
| **Modbus Bus** | Nested `ModbusConfig` — bus type, serial port, baud, parity, etc. Defaults match IQWS factory settings. | serial / 9600 8N1 |
| **Slave ID** | Modbus unit ID of the sensor (1–247). | `1` |
| **Poll Interval (seconds)** | Time between Modbus reads. | `3` |
| **Wind Speed Unit** | `kmh`, `mps`, or `knots`. Applies to `wind_speed` and `wind_gust` tags. | `kmh` |
| **Gust Window (seconds)** | Rolling-window size used to compute the peak wind speed. | `180` (3 min) |
| **No-Comms Timeout (seconds)** | Clears `comms_ok` after this many seconds without a successful read. | `30` |
| **Simulator App Key** | Optional. If set, read from the named simulator's tags instead of Modbus. Leave blank in production. | *(empty)* |

## Tags

### Readings (in the configured `display_unit`)

| Tag | Type | Description |
|---|---|---|
| `wind_speed` | number | Instantaneous wind speed. |
| `wind_gust` | number | Rolling-window max wind speed (see `gust_window_seconds`). |
| `wind_direction_degrees` | number | Direction in degrees (0–337.5°, 22.5° resolution). |
| `wind_direction_compass` | string | 16-point compass bearing — `N`, `NNE`, `NE`, …, `NNW`. |

### Diagnostics

| Tag | Type | Description |
|---|---|---|
| `comms_ok` | boolean | `true` while the sensor is responding. Cleared after `no_comms_timeout_seconds`. |
| `last_read_time` | number | Unix timestamp of the last successful read. |
| `raw_speed_value` | integer | Raw contents of holding register `0x0004` (speed × 100). |
| `raw_direction_index` | integer | Raw contents of holding register `0x0005` (0–15 compass index). |

### Technician commissioning (tag-only — no UI)

Set any of these tags to a non-null value and the app will issue the matching Modbus write to the sensor, then clear the tag and report the result in `last_cmd_result`. **Power-cycle the sensor for the change to take effect.**

| Tag | Type | Notes |
|---|---|---|
| `cmd_set_slave_id` | integer | 1–247. Writes register `0x0000`. |
| `cmd_set_baud` | integer | One of `2400, 4800, 9600, 19200, 38400, 57600, 115200`. Writes register `0x0001`. |
| `cmd_set_parity` | string | `none`, `odd`, or `even`. Writes register `0x0002`. |
| `last_cmd_result` | string | Populated by the app: `ok: …` or `error: …`. |

In simulator mode (`sim_app_key` set) these writes are rejected so you can't accidentally "reconfigure" a sensor that isn't there.

## Hardware

**Sensor:** IQFlow IQWS (Hunan Firstrate OEM), 12–30 VDC, RS-485 Modbus RTU, IP65, M12 4-pin connector.

**M12 RS-485 pinout:**

| Pin | Signal | Colour |
|---|---|---|
| 1 | +Vcc | brown |
| 2 | RS-485 A | white |
| 3 | GND | blue |
| 4 | RS-485 B | black |

**Factory serial defaults:** 9600 baud, 8 data bits, no parity, 1 stop bit, slave ID `0x01`.

## Modbus register map

| Address | FC | Type | Meaning | Scaling |
|---|---|---|---|---|
| `0x0000` | 03 / 06 | uint16 | Slave ID | — |
| `0x0001` | 03 / 06 | uint16 | Baud rate | `baud // 100` (e.g. 9600 → `0x0060`) |
| `0x0002` | 03 / 06 | uint16 | Parity | `0=none, 1=odd, 2=even` |
| `0x0004` | 03 | uint16 | Wind speed | `value / 100` m/s, range 0–50 m/s |
| `0x0005` | 03 | uint16 | Wind direction | 16-point compass index, 0–15, 22.5° resolution |

Direction is **not** a degree value on the wire — it's a 16-point compass index (0 = N, 2 = NE, 4 = E, 6 = SE, 8 = S, 10 = SW, 12 = W, 14 = NW; odd indices are the bisectors). The app does the `index × 22.5°` conversion.

Per the manual, registers outside the list above must not be accessed.

## Project layout

```
src/iqflow_wind_sensor/
  __init__.py          # Entry point — run_app(IQFlowWindSensorApplication())
  application.py       # Main loop, Modbus I/O, sim path, technician commands
  app_config.py        # Config schema (incl. ModbusConfig)
  app_tags.py          # Tag declarations
  app_ui.py            # UI definition
  iqws_driver.py       # Pure decode/encode helpers for the IQWS register map
  gust_tracker.py      # RollingMax for gust computation
simulators/sample/     # Wind-shaped tag simulator
tests/                 # pytest suite
```

## Need Help?

- Email: support@doover.com
- [Doover Documentation](https://docs.doover.com)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
