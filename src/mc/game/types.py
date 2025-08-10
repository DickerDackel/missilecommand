from enum import StrEnum, auto

import logging
logging.info(__name__)  # noqa: E402


class EIDs(StrEnum):
    PLAYER = auto()
    FLYER = auto()


class DebriefingPhase(StrEnum):
    SETUP = auto()
    LINGER_PRE = auto()
    MISSILES = auto()
    CITIES = auto()


class GamePhase(StrEnum):
    SETUP = auto()
    BRIEFING = auto()
    PLAYING = auto()
    END_OF_WAVE = auto()
    DEBRIEFING = auto()
    GAMEOVER = auto()
