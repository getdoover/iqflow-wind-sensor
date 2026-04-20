"""Tests for the RollingMax gust tracker."""

import pytest

from iqflow_wind_sensor.gust_tracker import RollingMax


def test_empty_window_returns_none():
    g = RollingMax(window_seconds=60)
    assert g.current(now=1000.0) is None


def test_single_sample_equals_current():
    g = RollingMax(window_seconds=60)
    g.add(7.5, now=100.0)
    assert g.current(now=100.0) == pytest.approx(7.5)


def test_max_wins_within_window():
    g = RollingMax(window_seconds=60)
    g.add(5.0, now=100.0)
    g.add(12.0, now=110.0)
    g.add(3.0, now=120.0)
    assert g.current(now=130.0) == pytest.approx(12.0)


def test_old_sample_evicted():
    g = RollingMax(window_seconds=10)
    g.add(99.0, now=100.0)
    g.add(5.0, now=115.0)
    # At now=118 the 99.0 sample is 18s old (evicted) and 5.0 is 3s old (kept).
    assert g.current(now=118.0) == pytest.approx(5.0)


def test_all_samples_eventually_evicted():
    g = RollingMax(window_seconds=5)
    g.add(10.0, now=100.0)
    g.add(20.0, now=101.0)
    assert g.current(now=200.0) is None


def test_add_none_does_not_crash_but_still_evicts():
    g = RollingMax(window_seconds=5)
    g.add(30.0, now=100.0)
    g.add(None, now=110.0)  # no-op for the value, but evicts old entries
    assert g.current(now=110.0) is None


def test_set_window_shrinks_and_evicts():
    g = RollingMax(window_seconds=100)
    g.add(50.0, now=100.0)
    g.add(1.0, now=150.0)
    assert g.current(now=150.0) == pytest.approx(50.0)
    # Shrink the window — 50.0 sample should fall off.
    g.set_window(10)
    assert g.current(now=150.0) == pytest.approx(1.0)


def test_reset_clears_samples():
    g = RollingMax(window_seconds=60)
    g.add(42.0, now=100.0)
    g.reset()
    assert g.current(now=100.0) is None


def test_invalid_window_rejected():
    with pytest.raises(ValueError):
        RollingMax(window_seconds=0)
    g = RollingMax(window_seconds=10)
    with pytest.raises(ValueError):
        g.set_window(-5)
