"""Tests for the pure iqws_driver decoding layer."""

import math

import pytest

from iqflow_wind_sensor.iqws_driver import (
    COMPASS_POINTS,
    DEGREES_PER_INDEX,
    IQWSVariant,
    WindUnit,
    convert_speed,
    decode,
    encode_baud,
    encode_parity,
    num_registers_for,
    unit_label,
    validate_slave_id,
)


# ---- decode -----------------------------------------------------------

def test_decode_combined_happy_path():
    # raw speed 528 -> 5.28 m/s, raw direction 2 -> NE / 45°
    reading = decode([528, 2], IQWSVariant.COMBINED)
    assert reading.speed_mps == pytest.approx(5.28)
    assert reading.direction_index == 2
    assert reading.direction_degrees == pytest.approx(45.0)
    assert reading.direction_compass == "NE"
    assert reading.raw_speed == 528
    assert reading.raw_direction == 2


def test_decode_speed_only_accepts_int():
    reading = decode(1000, IQWSVariant.SPEED_ONLY)
    assert reading.speed_mps == pytest.approx(10.0)
    assert reading.direction_index is None
    assert reading.direction_compass is None
    assert reading.raw_direction is None


def test_decode_combined_rejects_out_of_range_speed():
    # 50.01 m/s -> raw 5001, > WIND_SPEED_MAX_MPS after decode
    reading = decode([5001, 0], IQWSVariant.COMBINED)
    assert reading.speed_mps is None
    # Direction is still decoded independently.
    assert reading.direction_index == 0


def test_decode_combined_rejects_out_of_range_direction():
    reading = decode([1000, 99], IQWSVariant.COMBINED)
    assert reading.speed_mps == pytest.approx(10.0)
    assert reading.direction_index is None
    assert reading.direction_compass is None


def test_decode_none_is_blank_reading():
    reading = decode(None, IQWSVariant.COMBINED)
    assert reading.speed_mps is None
    assert reading.direction_index is None
    assert reading.raw_speed is None


def test_decode_speed_only_ignores_extra_registers():
    reading = decode([100, 5], IQWSVariant.SPEED_ONLY)
    assert reading.speed_mps == pytest.approx(1.0)
    assert reading.direction_index is None


@pytest.mark.parametrize("index", range(16))
def test_compass_table_round_trip(index):
    # Every index must map to a compass string and a degree value.
    reading = decode([0, index], IQWSVariant.COMBINED)
    assert reading.direction_compass == COMPASS_POINTS[index]
    assert reading.direction_degrees == pytest.approx(index * DEGREES_PER_INDEX)


def test_num_registers_for():
    assert num_registers_for(IQWSVariant.COMBINED) == 2
    assert num_registers_for(IQWSVariant.SPEED_ONLY) == 1


# ---- unit conversion --------------------------------------------------

def test_convert_speed_mps_identity():
    assert convert_speed(10.0, WindUnit.MPS) == pytest.approx(10.0)


def test_convert_speed_kmh():
    assert convert_speed(10.0, WindUnit.KMH) == pytest.approx(36.0)


def test_convert_speed_knots():
    # 10 m/s ≈ 19.438 kt
    assert convert_speed(10.0, WindUnit.KNOTS) == pytest.approx(19.4384, rel=1e-4)


def test_convert_speed_none_passthrough():
    assert convert_speed(None, WindUnit.KMH) is None


def test_unit_label():
    assert unit_label(WindUnit.MPS) == "m/s"
    assert unit_label(WindUnit.KMH) == "km/h"
    assert unit_label(WindUnit.KNOTS) == "kt"


# ---- commissioning encoders -------------------------------------------

@pytest.mark.parametrize(
    "baud,expected",
    [(2400, 0x24), (9600, 0x96), (19200, 0x192), (38400, 0x384), (57600, 0x576), (115200, 0x1152)],
)
def test_encode_baud_supported(baud, expected):
    assert encode_baud(baud) == expected


def test_encode_baud_rejects_unsupported():
    with pytest.raises(ValueError):
        encode_baud(12345)


@pytest.mark.parametrize("parity,expected", [("none", 0), ("odd", 1), ("even", 2), ("Odd", 1)])
def test_encode_parity(parity, expected):
    assert encode_parity(parity) == expected


def test_encode_parity_rejects_unknown():
    with pytest.raises(ValueError):
        encode_parity("whatever")


@pytest.mark.parametrize("slave_id", [1, 10, 247])
def test_validate_slave_id_accepts(slave_id):
    assert validate_slave_id(slave_id) == slave_id


@pytest.mark.parametrize("slave_id", [0, 248, -1, 1.5, "1"])
def test_validate_slave_id_rejects(slave_id):
    with pytest.raises(ValueError):
        validate_slave_id(slave_id)


def test_compass_points_are_22_5_spaced():
    # Sanity check on the compass table itself — 16 entries, 22.5° apart.
    assert len(COMPASS_POINTS) == 16
    assert math.isclose(DEGREES_PER_INDEX * 16, 360.0)
