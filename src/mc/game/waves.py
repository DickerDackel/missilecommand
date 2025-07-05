from typing import NamedTuple

import mc.globals as G


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
            *G.WAVES[widx],
            *G.FLYERS[fidx]
        )
        widx = (widx + 1) % len(G.WAVES)
        fidx = (fidx + 1) % len(G.FLYERS)
