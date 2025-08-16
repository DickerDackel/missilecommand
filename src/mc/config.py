import logging
logging.info(__name__)  # noqa: E402

from enum import IntEnum, auto
from importlib.resources import files
from types import SimpleNamespace
from typing import NamedTuple

import pygame

from ddframework.gridlayout import GridLayout
from pygame.math import Vector2 as vec2
from pygame.typing import ColorLike, Point

########################################################################
#     _                _ _           _   _
#    / \   _ __  _ __ | (_) ___ __ _| |_(_) ___  _ __
#   / _ \ | '_ \| '_ \| | |/ __/ _` | __| |/ _ \| '_ \
#  / ___ \| |_) | |_) | | | (_| (_| | |_| | (_) | | | |
# /_/   \_\ .__/| .__/|_|_|\___\__,_|\__|_|\___/|_| |_|
#         |_|   |_|
#
########################################################################

TITLE = 'mc'
SCREEN = pygame.Rect(0, 0, 256, 240)
FPS = 60

ASSETS = files('mc.assets')

GRID = GridLayout(SCREEN, 16, 16, 8, 8)

PLAY_AUDIO = True

########################################################################
#   ____
#  / ___|___  _ __ ___  _ __ ___   ___  _ __
# | |   / _ \| '_ ` _ \| '_ ` _ \ / _ \| '_ \
# | |__| (_) | | | | | | | | | | | (_) | | | |
#  \____\___/|_| |_| |_|_| |_| |_|\___/|_| |_|
#
########################################################################

COLOR = SimpleNamespace(
    ground='yellow',
    enemy_missile='red',
    defense_missile='blue',
    background='black',
    grid='grey',
    pause='blue',
    clear=(255, 255, 255, 0),
    score_color='red',
    gameover='#df3e23',
)

########################################################################
#  ____  _            _
# |  _ \| | __ _  ___(_)_ __   __ _
# | |_) | |/ _` |/ __| | '_ \ / _` |
# |  __/| | (_| | (__| | | | | (_| |
# |_|   |_|\__,_|\___|_|_| |_|\__, |
#                             |___/
#####################################################################)))

POS_GROUND = SCREEN.midbottom

BATTERY_RECT = pygame.Rect(0, 0, 16, 8)
POS_BATTERIES = [
    vec2(24, SCREEN.bottom - 28),
    vec2(SCREEN.centerx, SCREEN.bottom - 28),
    vec2(SCREEN.width - 24, SCREEN.bottom - 28),
]
BATTERY_SILO_OFFSET = vec2(0, 11)

_dx = 8
_dy = 3
SILO_OFFSETS = [
    #     #
    #    # #
    #   # # #
    #  # # # #
    vec2(0, -2 * _dy),
    vec2(-_dx / 2, -_dy), vec2(_dx / 2, -_dy),
    vec2(-_dx, 0), vec2(_dx, 0), vec2(0,  0),
    vec2(-1.5 * _dx, _dy), vec2(1.5 * _dx, _dy), vec2(-_dx / 2, _dy), vec2(_dx / 2, _dy),
]

POS_CITIES = [
    vec2( 56, SCREEN.bottom - 8 - 8 - 6),
    vec2( 80, SCREEN.bottom - 8 - 6 - 6),
    vec2(104, SCREEN.bottom - 8 - 9 - 6),
    vec2(154, SCREEN.bottom - 8 - 9 - 6),
    vec2(180, SCREEN.bottom - 8 - 6 - 6),
    vec2(206, SCREEN.bottom - 8 - 8 - 6),
]

HITBOX_CITY = [
    pygame.Rect(0, 0, 22, 12).move_to(center=POS_CITIES[i])
    for i in range(len(POS_CITIES))
]

HITBOX_BATTERIES = [
    pygame.Rect(0, 0, 16, 4).move_to(center=POS_BATTERIES[i])
    for i in range(len(POS_BATTERIES))
]


POS_MISSILES_DEBRIEFING = vec2(SCREEN.centerx - 15, SCREEN.centery)
POS_CITIES_DEBRIEFING = vec2(SCREEN.centerx - 15, 2 * SCREEN.height / 3)

########################################################################
#   ____                        ____       _   _   _
#  / ___| __ _ _ __ ___   ___  / ___|  ___| |_| |_(_)_ __   __ _ ___
# | |  _ / _` | '_ ` _ \ / _ \ \___ \ / _ \ __| __| | '_ \ / _` / __|
# | |_| | (_| | | | | | |  __/  ___) |  __/ |_| |_| | | | | (_| \__ \
#  \____|\__,_|_| |_| |_|\___| |____/ \___|\__|\__|_|_| |_|\__, |___/
#                                                          |___/
#######################################################################)

EXPLOSION_DURATION = 0.5
EXPLOSION_COLORS = ('white', '#ffd541', '#a6fcdb', '#df3e23', '#20d6c7', '#d6f264')

KEY_SILO_MAP = {
    pygame.K_q: 0,
    pygame.K_w: 1,
    pygame.K_e: 2,
}

MISSILE_SPEEDS = [136, 272, 136]


class Score(IntEnum):
    UNUSED_MISSILE = 5
    MISSILE = 20
    CITY = 100
    PLANE = 100
    SATELLITE = 100
    SMART_BOMB = 125

########################################################################
#  ____             _ _
# / ___| _ __  _ __(_) |_ ___  ___
# \___ \| '_ \| '__| | __/ _ \/ __|
#  ___) | |_) | |  | | ||  __/\__ \
# |____/| .__/|_|  |_|\__\___||___/
#       |_|
########################################################################


SPRITESHEET = {
    'crosshair': pygame.Rect(0, 0, 7, 7),
    'missiles': [pygame.Rect(16, 0, 4, 3), pygame.Rect(24, 0, 4, 3),
                 pygame.Rect(16, 8, 4, 3), pygame.Rect(24, 8, 4, 3)],
    'city': pygame.Rect(32, 0, 22, 12),
    'cities': [pygame.Rect(0, 72, 22, 12), pygame.Rect(32, 72, 22, 12),
               pygame.Rect(64, 72, 22, 12), pygame.Rect(96, 72, 22, 12)],
    'ruin': pygame.Rect(64, 0, 22, 12),
    'ruins': [pygame.Rect(0, 88, 22, 12), pygame.Rect(32, 88, 22, 12),
              pygame.Rect(64, 88, 22, 12), pygame.Rect(96, 88, 22, 12)],
    'alien_big_green': pygame.Rect(96, 0, 16, 16),
    'alien_big_red': pygame.Rect(112, 0, 16, 16),
    'alien_green': pygame.Rect(128, 0, 16, 16),
    'alien_red': pygame.Rect(144, 0, 16, 16),
    'plane_green': pygame.Rect(160, 0, 16, 16),
    'plane_red': pygame.Rect(176, 0, 16, 16),
    'smartbomb_green': pygame.Rect(192, 0, 16, 16),
    'smartbomb_red': pygame.Rect(200, 0, 16, 16),
    'missile-heads': [pygame.Rect(128, 72, 3, 3), pygame.Rect(136, 72, 3, 3),
                      pygame.Rect(144, 72, 3, 3), pygame.Rect(128, 80, 3, 3),
                      pygame.Rect(136, 80, 3, 3), pygame.Rect(144, 80, 3, 3)],
    'targets': [pygame.Rect(232, 0, 7, 7), pygame.Rect(240, 0, 7, 7),
                pygame.Rect(248, 0, 7, 7), pygame.Rect(232, 8, 7, 7),
                pygame.Rect(240, 8, 7, 7), pygame.Rect(248, 8, 7, 7)],
    'ground': pygame.Rect(0, 16, 256, 32),
    'explosions': [pygame.Rect(256, 0, 32, 32), pygame.Rect(288, 0, 32, 32),
                   pygame.Rect(320, 0, 32, 32), pygame.Rect(352, 0, 32, 32),
                   pygame.Rect(384, 0, 32, 32), pygame.Rect(416, 0, 32, 32)],
    'gameover-small': [pygame.Rect(256, 32, 32, 32), pygame.Rect(288, 32, 32, 32),
                       pygame.Rect(320, 32, 32, 32), pygame.Rect(352, 32, 32, 32),
                       pygame.Rect(384, 32, 32, 32), pygame.Rect(416, 32, 32, 32)],
    'gameover': pygame.Rect(256, 64, 128, 128),
    'letters': [pygame.Rect(0, 48, 8, 8), pygame.Rect(8, 48, 8, 8),
                pygame.Rect(16, 48, 8, 8), pygame.Rect(24, 48, 8, 8),
                pygame.Rect(32, 48, 8, 8), pygame.Rect(40, 48, 8, 8),
                pygame.Rect(48, 48, 8, 8), pygame.Rect(56, 48, 8, 8),
                pygame.Rect(64, 48, 8, 8), pygame.Rect(72, 48, 8, 8),
                pygame.Rect(80, 48, 8, 8), pygame.Rect(88, 48, 8, 8),
                pygame.Rect(96, 48, 8, 8), pygame.Rect(104, 48, 8, 8),
                pygame.Rect(112, 48, 8, 8), pygame.Rect(120, 48, 8, 8),
                pygame.Rect(128, 48, 8, 8), pygame.Rect(136, 48, 8, 8),
                pygame.Rect(144, 48, 8, 8), pygame.Rect(152, 48, 8, 8),
                pygame.Rect(160, 48, 8, 8), pygame.Rect(168, 48, 8, 8),
                pygame.Rect(176, 48, 8, 8), pygame.Rect(184, 48, 8, 8),
                pygame.Rect(192, 48, 8, 8), pygame.Rect(200, 48, 8, 8),
                pygame.Rect(0, 56, 8, 8), pygame.Rect(8, 56, 8, 8),
                pygame.Rect(16, 56, 8, 8), pygame.Rect(24, 56, 8, 8),
                pygame.Rect(32, 56, 8, 8), pygame.Rect(40, 56, 8, 8),
                pygame.Rect(48, 56, 8, 8), pygame.Rect(56, 56, 8, 8),
                pygame.Rect(64, 56, 8, 8), pygame.Rect(72, 56, 8, 8),
                pygame.Rect(80, 56, 8, 8), pygame.Rect(88, 56, 8, 8),
                pygame.Rect(96, 56, 8, 8), pygame.Rect(104, 56, 8, 8),
                pygame.Rect(112, 56, 8, 8), pygame.Rect(120, 56, 8, 8),
                pygame.Rect(128, 56, 8, 8), pygame.Rect(136, 56, 8, 8),
                pygame.Rect(144, 56, 8, 8), pygame.Rect(152, 56, 8, 8),
                pygame.Rect(160, 56, 8, 8), pygame.Rect(168, 56, 8, 8),
                pygame.Rect(176, 56, 8, 8)],
    'red': pygame.Rect(0, 64, 8, 8),
    'green': pygame.Rect(8, 64, 8, 8),
    'blue': pygame.Rect(16, 64, 8, 8),
    'cyan': pygame.Rect(24, 64, 8, 8),
    'magenta': pygame.Rect(32, 64, 8, 8),
    'yellow': pygame.Rect(40, 64, 8, 8),
}

CHAR_MAP = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
            'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14,
            'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21,
            'W': 22, 'X': 23, 'Y': 24, 'Z': 25, '0': 26, '1': 27, '2': 28,
            '3': 29, '4': 30, '5': 31, '6': 32, '7': 33, '8': 34, '9': 35,
            'up': 36, 'down': 37, 'left': 38, 'right': 39, 'copy': 40, 'popy': 41,
            ' ': 42, '.': 43, ',': 44, '!': 45, ':': 46, ';': 47, 'x': 48}


########################################################################
#
# | |    _____   _____| |___
# | |   / _ \ \ / / _ \ / __|
# | |__|  __/\ V /  __/ \__ \
# |_____\___| \_/ \___|_|___/
#
########################################################################

# Initial data from the original Missile Command disassembly table was delay
# frames.  I wanted to preserve the original values and thus added the `60 * `
# to convert it into pixels/s
WAVES = [
    (12, 60 / 4.8125, 0),
    (15, 60 / 2.875, 0),
    (18, 60 / 1.75, 0),
    (12, 60 / 1.03, 0),
    (16, 60 / 0.625, 0),
    (14, 60 / 0.375, 1),
    (17, 60 / 0.25, 1),
    (10, 60 / 0.125, 2),
    (13, 60 / 0.0625, 3),
    (16, 60 / 0.04, 4),
    (19, 60 / 0.02, 4),
    (12, 60 / 0.016, 5),
    (14, 60 / 0.008, 5),
    (16, 60 / 0.004, 6),
    (18, 60, 6),
    (14, 60, 7),
    (17, 60, 7),
    (19, 60, 7),
    (22, 60, 7),
]

# For the cooldown below, the same as for the frame delay above applies
FLYERS = [
    (0, 0, 0, 0),
    (SCREEN.height - 148, SCREEN.height - 195, 240 / 60, 128 / 60),
    (SCREEN.height - 148, SCREEN.height - 195, 160 / 60, 96 / 60),
    (SCREEN.height - 132, SCREEN.height - 163, 128 / 60, 64 / 60),
    (SCREEN.height - 132, SCREEN.height - 163, 128 / 60, 48 / 60),
    (SCREEN.height - 100, SCREEN.height - 131,  96 / 60, 32 / 60),
    (SCREEN.height - 100, SCREEN.height - 131,  64 / 60, 32 / 60),
    (SCREEN.height - 100, SCREEN.height - 131,  32 / 60, 16 / 60),
]

MISSILES_PER_WAVE = 4
MISSILE_SPLITS = 3
PLANE_SPEED = 20
SATELLITE_SPEED = 30

CITY_ATTACKS = 3
SILO_ATTACKS = 3


########################################################################
#  _____                 _
# | ____|_   _____ _ __ | |_ ___
# |  _| \ \ / / _ \ '_ \| __/ __|
# | |___ \ V /  __/ | | | |_\__ \
# |_____| \_/ \___|_| |_|\__|___/
#
########################################################################

class Events(IntEnum):
    ADD_SCORE = auto()


########################################################################
# _____         _
# |_   _|____  _| |_ ___
#  | |/ _ \ \/ / __/ __|
#  | |  __/>  <| |_\__ \
#  |_|\___/_/\_\\__|___/
#
########################################################################

# Original y coordinates left in, but since line 0 is at the bottom, all are
# 240 - y


class MessageConfig(NamedTuple):
    text: str
    pos: Point
    anchor: str
    color: ColorLike = 'white'
    scale: tuple[float, float] = (1, 1)


MESSAGES = {
    "PAUSE": MessageConfig("PAUSE", GRID(7, 4, 2, 2).center, "center", "blue", (3, 3)),
    "PLAYER": MessageConfig("PLAYER  ", GRID(7, 4, 2, 2).center, "center", "blue"),
    "PLAYER_NO": MessageConfig("       1", GRID(7, 4, 2, 2).center, "center", "red"),
    "x POINTS": MessageConfig("  x POINTS", GRID.center, "center", "blue"),
    "MULT": MessageConfig("1         ", GRID.center, "center", "red"),
    "DEFEND CITIES": MessageConfig("DEFEND      CITIES", (GRID.centerx, 2 * GRID.height / 3), "center", "blue"),  # noqa: E501
    "BONUS POINTS": MessageConfig("BONUS POINTS", (80, 240 - 160), "center", "blue"),
    "SCORE": MessageConfig("SCORE", GRID(7, 0, 2, 1).midbottom, "midbottom", "red"),
}
