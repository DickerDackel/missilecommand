from enum import IntEnum, auto
from importlib.resources import files
from types import SimpleNamespace

import pygame

from pygame import Vector2 as v2

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

########################################################################
#   ____
#  / ___|___  _ __ ___  _ __ ___   ___  _ __
# | |   / _ \| '_ ` _ \| '_ ` _ \ / _ \| '_ \
# | |__| (_) | | | | | | | | | | | (_) | | | |
#  \____\___/|_| |_| |_|_| |_| |_|\___/|_| |_|
#
########################################################################

COLOR = SimpleNamespace(
    ground = 'yellow',
    enemy_missile = 'red',
    own_missile ='blue',
    background='black',
    grid='grey',
    clear=(255, 255, 255, 0),
)

BASE_FONT = 'DSEG14Classic-Regular.ttf'
_font = ASSETS.joinpath(BASE_FONT)
pygame.font.init()
FONT = SimpleNamespace(
    normal=pygame.Font(_font, 8)
)
for f in FONT.__dict__.values():
    f.align = pygame.FONT_CENTER

########################################################################
#   ____                        ____       _   _   _
#  / ___| __ _ _ __ ___   ___  / ___|  ___| |_| |_(_)_ __   __ _ ___
# | |  _ / _` | '_ ` _ \ / _ \ \___ \ / _ \ __| __| | '_ \ / _` / __|
# | |_| | (_| | | | | | |  __/  ___) |  __/ |_| |_| | | | | (_| \__ \
#  \____|\__,_|_| |_| |_|\___| |____/ \___|\__|\__|_|_| |_|\__, |___/
#                                                          |___/
########################################################################

POS_BATTERIES = [
    v2(24, SCREEN.bottom - 16),
    v2(SCREEN.centerx, SCREEN.bottom - 16),
    v2(SCREEN.width - 24, SCREEN.bottom - 16),
]

POS_LAUNCHPADS = [pos + (0, -11) for pos in POS_BATTERIES]

POS_GROUND = SCREEN.midbottom
POS_CITIES = [
    v2( 56, SCREEN.bottom - 8 - 8),
    v2( 80, SCREEN.bottom - 8 - 6),
    v2(104, SCREEN.bottom - 8 - 9),
    v2(154, SCREEN.bottom - 8 - 9),
    v2(180, SCREEN.bottom - 8 - 6),
    v2(206, SCREEN.bottom - 8 - 8),
]

POS_MISSILES_DEBRIEFING = v2(SCREEN.centerx - 15, SCREEN.centery)
POS_CITIES_DEBRIEFING = v2(SCREEN.centerx - 15, 2 * SCREEN.height / 3) 

KEY_SILO_MAP = {
    pygame.K_q: 0,
    pygame.K_w: 1,
    pygame.K_e: 2,
}

NUMBER_OF_MISSILES = 15

_dx = 8
_dy = 3
MISSILE_OFFSETS = [
    #     #
    #    # #
    #   # # #
    #  # # # #
    (0, -2 * _dy),
    (-_dx / 2, -_dy), (_dx / 2, -_dy),
    (-_dx, 0), (_dx, 0), (0,  0),
    (-1.5 * _dx, _dy), (1.5 * _dx, _dy), (-_dx / 2, _dy), (_dx / 2, _dy),
]

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
    'missiles': [pygame.Rect(16, 0, 4, 3), pygame.Rect(24, 0, 4, 3), pygame.Rect(16, 8, 4, 3), pygame.Rect(24, 8, 4, 3)],
    'city': pygame.Rect(32, 0, 22, 12),
    'ruins': pygame.Rect(64, 0, 22, 12),
    'alien_big_green': pygame.Rect(96, 0, 16, 16),
    'alien_big_red': pygame.Rect(112, 0, 16, 16),
    'alien_green': pygame.Rect(128, 0, 16, 16),
    'alien_red': pygame.Rect(144, 0, 16, 16),
    'plane_green': pygame.Rect(160, 0, 16, 16),
    'plane_red': pygame.Rect(176, 0, 16, 16),
    'smartbomb_green': pygame.Rect(192, 0, 16, 16),
    'smartbomb_red': pygame.Rect(200, 0, 16, 16),
    'missile-heads': [pygame.Rect(208, 0, 1, 1), pygame.Rect(216, 0, 1, 1), pygame.Rect(224, 0, 1, 1),
                      pygame.Rect(208, 8, 1, 1), pygame.Rect(216, 8, 1, 1), pygame.Rect(224, 8, 1, 1)],
    'targets': [pygame.Rect(232, 0, 7, 7), pygame.Rect(240, 0, 7, 7), pygame.Rect(248, 0, 7, 7),
                pygame.Rect(232, 8, 7, 7), pygame.Rect(240, 8, 7, 7), pygame.Rect(248, 8, 7, 7)],
    'ground': pygame.Rect(0, 16, 256, 32),
    'explosion': [pygame.Rect(256, 0, 32, 32), pygame.Rect(288, 0, 32, 32),
                  pygame.Rect(320, 0, 32, 32), pygame.Rect(352, 0, 32, 32),
                  pygame.Rect(384, 0, 32, 32), pygame.Rect(416, 0, 32, 32)],
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
    (0, 0, 0, 60 * 0),
    (148, 195, 240, 60 * 128),
    (148, 195, 160, 60 * 96),
    (132, 163, 128, 60 * 64),
    (132, 163, 128, 60 * 48),
    (100, 131, 96, 60 * 32),
    (100, 131, 64, 60 * 32),
    (100, 131, 32, 60 * 16),
]

MISSILES_PER_WAVE = 4
MISSILE_SPLITS = 3
BOMBER_SPEED = 20
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
MESSAGES = {
    'PLAYER': ((96, 240 - 144), (1, 1 ), 'blue'),
    'x POINTS': ((104, 240 - 112), (1, 1), 'blue'),
    'DEFEND CITIES': ((56, 240 - 56), (1, 1), 'blue'),
    'BONUS POINTS': ((80, 240 - 160), (1, 1), 'blue'),
    'SCORE': ((128, 10), (1, 1), 'red'),
}
