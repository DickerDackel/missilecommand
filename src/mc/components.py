from dataclasses import dataclass, field
from enum import IntEnum, auto

from pygame import Vector2 as vec2

from pgcooldown import LerpThing


class Comp(IntEnum):
    ANCHOR = auto()
    BATTERY_ID = auto()
    COLOR = auto()
    EXPLOSION_SCALE = auto()
    ID = auto()
    IS_BATTERY = auto()
    IS_CITY = auto()
    IS_DEAD_TRAIL = auto()
    IS_DEFENSE = auto()
    IS_EXPLOSION = auto()
    IS_MISSILE = auto()
    IS_MISSILE_HEAD = auto()
    IS_RUIN = auto()
    IS_SILO = auto()
    IS_TARGET = auto()
    IS_TEXT = auto()
    LERPTHING = auto()
    LERPTHING_LIST = auto()
    MOMENTUM = auto()
    PRSA = auto()
    RECT = auto()
    SILO_ID = auto()
    SPEED = auto()
    SPRITE = auto()
    TARGET = auto()
    TEXT = auto()
    TEXTURE = auto()
    TEXTURES = auto()
    TRAIL = auto()
    WANTS_MOUSE = auto()


@dataclass
class PRSA:
    pos: vec2 = field(default_factory=vec2)
    rotation: float = 0
    scale: float | tuple[float, float] = (1, 1)
    alpha: float = 255

    def __post_init__(self):
        if not isinstance(self.pos, vec2):
            self.pos = vec2(self.pos)

    def __iter__(self):
        yield self.pos
        yield self.rotation
        yield self.scale
        yield self.alpha


class AutoCycle:
    def __init__(self, duration, items, *, repeat=1):
        self.index = LerpThing(0, len(items), duration, repeat=repeat)
        self.items = items.copy()

    def __call__(self):
        return self.items[int(self.index())]
