from enum import IntEnum, auto

class Comp(IntEnum):
    POS = auto()
    TEXTURE = auto()
    RECT = auto()

    WANTS_MOUSE = auto()
