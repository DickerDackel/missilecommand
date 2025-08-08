import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Iterator
from itertools import cycle
from typing import NamedTuple

import mc.config as C


class Wave(NamedTuple):
    missiles: int
    missile_speed: float
    smartbombs: int
    flyer_min_height: int
    flyer_max_height: int
    flyer_cooldown: int
    flyer_fire_cooldown: int


def wave_iter() -> Iterator[Wave]:
    wave = cycle(C.WAVES)
    flyer = cycle(C.FLYERS)
    while True:
        yield Wave(*next(wave), *next(flyer))
