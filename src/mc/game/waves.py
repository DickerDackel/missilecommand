from typing import NamedTuple

import mc.config as C


class Wave(NamedTuple):
    missiles: int
    missile_speed: float
    smartbombs: int
    flyer_min_height: int
    flyer_max_height: int
    flyer_cooldown: int
    flyer_fire_rate: int

def wave_iter():
    widx = 0
    fidx = 0
    while True:
        yield Wave(
            *C.WAVES[widx],
            *C.FLYERS[fidx]
        )
        widx = (widx + 1) % len(C.WAVES)
        fidx = (fidx + 1) % len(C.FLYERS)
