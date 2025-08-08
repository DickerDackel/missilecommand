from enum import IntEnum, StrEnum, auto

import logging
logging.info(__name__)  # noqa: E402


class Comp(IntEnum):
    ANCHOR = auto()
    BATTERY_ID = auto()
    COLOR = auto()
    CONTAINER = auto()
    EXPLOSION_SCALE = auto()
    FLYER_FIRE_COOLDOWN = auto()
    ID = auto()
    IS_BATTERY = auto()
    IS_CITY = auto()
    IS_DEAD = auto()
    IS_DEAD_TRAIL = auto()
    IS_DEFENSE = auto()
    IS_EXPLOSION = auto()
    IS_FLYER = auto()
    IS_MISSILE = auto()
    IS_MISSILE_HEAD = auto()
    IS_MISSILE_TRAIL = auto()
    IS_RUIN = auto()
    IS_SILO = auto()
    IS_TARGET = auto()
    IS_TEXT = auto()
    LERPTHING = auto()
    LERPTHING_LIST = auto()
    MOMENTUM = auto()
    NOTIFY_DEAD = auto()
    PRSA = auto()
    RECT = auto()
    SHUTDOWN = auto()
    SILO_ID = auto()
    SPEED = auto()
    SPRITE = auto()
    TARGET = auto()
    TEXT = auto()
    TEXTURE = auto()
    TEXTURES = auto()
    TRAIL = auto()
    WANTS_MOUSE = auto()
    LINGER_POST = auto()


class DebriefingPhase(IntEnum):
    SETUP = auto()
    LINGER_PRE = auto()
    MISSILES = auto()
    CITIES = auto()


class EIDs(StrEnum):
    PLAYER = 'player'
    FLYER = 'flyer'


class GamePhase(IntEnum):
    SETUP = auto()
    BRIEFING = auto()
    PLAYING = auto()
    END_OF_WAVE = auto()
    DEBRIEFING = auto()
    GAMEOVER = auto()
