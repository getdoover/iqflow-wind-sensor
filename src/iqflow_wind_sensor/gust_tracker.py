"""Rolling-window maximum for wind gust tracking."""

from __future__ import annotations

import time
from collections import deque


class RollingMax:
    """Tracks the maximum of timestamped samples within a rolling window.

    Samples older than ``window_seconds`` are evicted on each ``add()`` /
    ``current()`` call. Returns ``None`` when the window is empty.
    """

    def __init__(self, window_seconds: float):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._window = float(window_seconds)
        self._samples: deque[tuple[float, float]] = deque()

    @property
    def window_seconds(self) -> float:
        return self._window

    def set_window(self, window_seconds: float) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._window = float(window_seconds)

    def add(self, value: float | None, now: float | None = None) -> None:
        if value is None:
            self._evict(now if now is not None else time.time())
            return
        ts = now if now is not None else time.time()
        self._samples.append((ts, float(value)))
        self._evict(ts)

    def current(self, now: float | None = None) -> float | None:
        self._evict(now if now is not None else time.time())
        if not self._samples:
            return None
        return max(v for _, v in self._samples)

    def reset(self) -> None:
        self._samples.clear()

    def _evict(self, now: float) -> None:
        cutoff = now - self._window
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()
