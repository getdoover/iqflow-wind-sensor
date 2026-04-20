"""Pure decoding / encoding helpers for the IQFlow IQWS wind sensor.

Register map (holding registers, FC 0x03 read / 0x06 write):
    0x0000  slave id         uint16
    0x0001  baud             uint16, BCD-packed baud // 100 (e.g. 9600 -> 0x0096, 19200 -> 0x0192)
    0x0002  parity           uint16 (0=none, 1=odd, 2=even)
    0x0004  wind speed       uint16, value / 100 -> m/s     [0 .. 50 m/s]
    0x0005  wind direction   uint16, 16-point compass index [0 .. 15]

Direction is NOT degrees on the wire — it's a 16-point compass index with
22.5° resolution (0 = N, 2 = NE, 4 = E, 6 = SE, 8 = S, 10 = SW, 12 = W, 14 = NW;
odd indices are the bisectors).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

REG_SLAVE_ID = 0x0000
REG_BAUD = 0x0001
REG_PARITY = 0x0002
REG_WIND_SPEED = 0x0004
REG_WIND_DIRECTION = 0x0005

WIND_SPEED_MAX_MPS = 50.0
WIND_DIRECTION_MAX_INDEX = 15
DEGREES_PER_INDEX = 22.5

COMPASS_POINTS = (
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
)


class IQWSVariant(str, enum.Enum):
    COMBINED = "combined"       # wind speed + direction (IQWS-D / SD-A)
    SPEED_ONLY = "speed_only"   # wind speed only (IQWS-S)


@dataclass(frozen=True)
class IQWSReading:
    speed_mps: float | None
    direction_index: int | None
    direction_degrees: float | None
    direction_compass: str | None
    raw_speed: int | None
    raw_direction: int | None


def decode(registers: list[int] | int | None, variant: IQWSVariant) -> IQWSReading:
    """Decode a register block starting at REG_WIND_SPEED (0x0004).

    ``registers`` is what pydoover's ``ModbusInterface.read_registers`` returns:
    a list[int] for >1 register, an int for a single register, or None on failure.

    For COMBINED we expect 2 registers (speed @ 0x0004, direction @ 0x0005).
    For SPEED_ONLY we expect 1 register (speed @ 0x0004).
    """
    if registers is None:
        return IQWSReading(None, None, None, None, None, None)

    if isinstance(registers, int):
        values = [registers]
    else:
        values = list(registers)

    raw_speed = values[0] if len(values) >= 1 else None
    raw_direction = values[1] if variant is IQWSVariant.COMBINED and len(values) >= 2 else None

    speed_mps = _decode_speed(raw_speed)
    direction_index = _decode_direction_index(raw_direction)
    direction_degrees = direction_index * DEGREES_PER_INDEX if direction_index is not None else None
    direction_compass = COMPASS_POINTS[direction_index] if direction_index is not None else None

    return IQWSReading(
        speed_mps=speed_mps,
        direction_index=direction_index,
        direction_degrees=direction_degrees,
        direction_compass=direction_compass,
        raw_speed=raw_speed,
        raw_direction=raw_direction,
    )


def _decode_speed(raw: int | None) -> float | None:
    if raw is None:
        return None
    speed = raw / 100.0
    if speed < 0 or speed > WIND_SPEED_MAX_MPS:
        return None
    return speed


def _decode_direction_index(raw: int | None) -> int | None:
    if raw is None:
        return None
    if raw < 0 or raw > WIND_DIRECTION_MAX_INDEX:
        return None
    return raw


def num_registers_for(variant: IQWSVariant) -> int:
    return 2 if variant is IQWSVariant.COMBINED else 1


# ---- unit conversions ---------------------------------------------------

_MPS_TO_KMH = 3.6
_MPS_TO_KNOTS = 1.9438444924406046


class WindUnit(str, enum.Enum):
    MPS = "mps"
    KMH = "kmh"
    KNOTS = "knots"


def convert_speed(speed_mps: float | None, unit: WindUnit) -> float | None:
    if speed_mps is None:
        return None
    if unit is WindUnit.MPS:
        return speed_mps
    if unit is WindUnit.KMH:
        return speed_mps * _MPS_TO_KMH
    if unit is WindUnit.KNOTS:
        return speed_mps * _MPS_TO_KNOTS
    raise ValueError(f"Unknown wind unit: {unit}")


def unit_label(unit: WindUnit) -> str:
    return {
        WindUnit.MPS: "m/s",
        WindUnit.KMH: "km/h",
        WindUnit.KNOTS: "kt",
    }[unit]


# ---- commissioning encoders (for technician write tags) -----------------

_BAUD_CHOICES = (2400, 4800, 9600, 19200, 38400, 57600, 115200)
_PARITY_CHOICES = {"none": 0, "odd": 1, "even": 2}


def encode_baud(baud: int) -> int:
    """Encode a baud rate into the IQWS baud register.

    The sensor stores baud // 100 as BCD — each decimal digit occupies one
    nibble. e.g. 9600 → 0x0096 (= 150 dec), 19200 → 0x0192 (= 402 dec).
    """
    if baud not in _BAUD_CHOICES:
        raise ValueError(f"Unsupported baud {baud!r}; expected one of {_BAUD_CHOICES}")
    return int(str(baud // 100), 16)


def encode_parity(parity: str) -> int:
    key = (parity or "").strip().lower()
    if key not in _PARITY_CHOICES:
        raise ValueError(f"Unsupported parity {parity!r}; expected one of {list(_PARITY_CHOICES)}")
    return _PARITY_CHOICES[key]


def validate_slave_id(slave_id: int) -> int:
    if not isinstance(slave_id, int) or slave_id < 1 or slave_id > 247:
        raise ValueError(f"Slave id must be an int in 1..247, got {slave_id!r}")
    return slave_id
