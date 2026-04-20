"""Simulator that emits IQWS-shaped raw register values via tags.

The real app, when ``sim_app_key`` is configured, reads these tags instead
of hitting the Modbus bus. Values mirror the format the sensor itself
returns over Modbus:

    sim_wind_speed_raw      uint16, wind speed * 100  (e.g. 528 -> 5.28 m/s)
    sim_wind_direction_raw  uint16, 16-point compass index (0..15)
"""

import math
import random

from pydoover.docker import Application, run_app
from pydoover.tags import Tag, Tags


class WindSimulatorTags(Tags):
    sim_wind_speed_raw = Tag("integer", default=0)
    sim_wind_direction_raw = Tag("integer", default=0)


class WindSimulator(Application):
    tags_cls = WindSimulatorTags
    loop_target_period = 1

    async def setup(self):
        # Seed a meandering wind vector so values look more realistic than
        # pure uniform noise.
        self._speed_mps = random.uniform(2.0, 8.0)
        self._direction_index = random.randint(0, 15)
        self._tick = 0

    async def main_loop(self):
        self._tick += 1

        # Wind speed: slow random walk with an occasional gust, clipped to
        # the sensor's 0..50 m/s range.
        drift = random.gauss(0.0, 0.3)
        if random.random() < 0.03:
            drift += random.uniform(3.0, 8.0)  # gust
        self._speed_mps = max(0.0, min(50.0, self._speed_mps + drift))
        # Gentle pull toward a mean so we don't wander off to 50 m/s.
        self._speed_mps += (5.0 - self._speed_mps) * 0.02

        # Direction: slowly rotates, with small probability of a bigger shift.
        if random.random() < 0.1:
            self._direction_index = (self._direction_index + random.choice((-1, 1))) % 16
        if random.random() < 0.01:
            self._direction_index = random.randint(0, 15)

        raw_speed = int(round(self._speed_mps * 100))
        raw_direction = int(self._direction_index)

        await self.tags.sim_wind_speed_raw.set(raw_speed)
        await self.tags.sim_wind_direction_raw.set(raw_direction)

    # Keep the gust boost around the "spin" of gaussian noise balanced even
    # if Python's random isn't perfectly centred.
    @staticmethod
    def _smoothstep(x: float) -> float:
        return 0.5 * (1 - math.cos(math.pi * x))


def main():
    """Run the IQWS wind simulator application."""
    run_app(WindSimulator())


if __name__ == "__main__":
    main()
