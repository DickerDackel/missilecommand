from enum import IntEnum

class GamePhase(IntEnum):
    SETUP = 1
    BRIEFING = 2
    PLAYING = 3
    END_OF_WAVE = 4
    DEBRIEFING= 5
    GAMEOVER = 6

class DebriefingPhase(IntEnum):
    SETUP = 1
    LINGER_PRE = 2
    MISSILES = 3
    CITIES = 4
    LINGER_POST = 5
