import logging
logging.info(__name__)  # noqa: E402

from pathlib import Path
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

GRID_WIDTH, GRID_HEIGHT = 31, 26
GRID = GridLayout(SCREEN, GRID_WIDTH, GRID_HEIGHT, 0, 0)
CONTAINER = SCREEN.inflate(16, 16)

PLAY_AUDIO = True

VENDOR = 'dackelsoft'
APPNAME = 'Missile Command'
STATE_DIRECTORY = Path(pygame.system.get_pref_path(VENDOR, APPNAME))
HIGHSCORE_FILE = STATE_DIRECTORY / 'missile command highscores.json'

########################################################################
#   ____
#  / ___|___  _ __ ___  _ __ ___   ___  _ __
# | |   / _ \| '_ ` _ \| '_ ` _ \ / _ \| '_ \
# | |__| (_) | | | | | | | | | | | (_) | | | |
#  \____\___/|_| |_| |_|_| |_| |_|\___/|_| |_|
#
########################################################################

COLOR = SimpleNamespace(
    background='black',
    clear=(255, 255, 255, 0),
    defense_missile='blue',
    enemy_missile='red',
    gameover='#df3e23',
    grid='grey',
    initials='yellow',
    normal_text='blue',
    score_color='red',
    special_text='red',
    title='white'
)

########################################################################
#  ____  _            _
# |  _ \| | __ _  ___(_)_ __   __ _
# | |_) | |/ _` |/ __| | '_ \ / _` |
# |  __/| | (_| | (__| | | | | (_| |
# |_|   |_|\__,_|\___|_|_| |_|\__, |
#                             |___/
#####################################################################)))

CROSSHAIR_CONSTRAINT = pygame.Rect(0, 0, 256, 200).move_to(midtop=SCREEN.midtop)

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


POS_MISSILES_DEBRIEFING = vec2(GRID(16, 12, 1, 1).midleft)
POS_CITIES_DEBRIEFING = vec2(GRID(16, 15, 1, 1).midleft)
POS_MISSILES_SCORE_DEBRIEFING = vec2(GRID(14, 12, 1, 1).midright)
POS_CITIES_SCORE_DEBRIEFING = vec2(GRID(14, 15, 1, 1).midright)

########################################################################
#   ____                        ____       _   _   _
#  / ___| __ _ _ __ ___   ___  / ___|  ___| |_| |_(_)_ __   __ _ ___
# | |  _ / _` | '_ ` _ \ / _ \ \___ \ / _ \ __| __| | '_ \ / _` / __|
# | |_| | (_| | | | | | |  __/  ___) |  __/ |_| |_| | | | | (_| \__ \
#  \____|\__,_|_| |_| |_|\___| |____/ \___|\__|\__|_|_| |_|\__, |___/
#                                                          |___/
#######################################################################)

EXPLOSION_RADIUS = 16
EXPLOSION_DURATION = 1.5
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
    SMARTBOMB = 125


HIGHSCORE_ENTRY_SCROLL_COOLDOWN = 0.125
BONUS_CITY_SCORE = 10_000
MAX_SCORE_MULT = 6

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
    'small-cities': [pygame.Rect(0, 104, 16, 9), pygame.Rect(16, 104, 16, 9),
                     pygame.Rect(32, 104, 16, 9), pygame.Rect(48, 104, 16, 9)],
    'ruin': pygame.Rect(64, 0, 22, 12),
    'ruins': [pygame.Rect(0, 88, 22, 12), pygame.Rect(32, 88, 22, 12),
              pygame.Rect(64, 88, 22, 12), pygame.Rect(96, 88, 22, 12)],
    'small-ruins': [pygame.Rect(0, 120, 16, 9), pygame.Rect(16, 120, 16, 9),
                    pygame.Rect(32, 120, 16, 9), pygame.Rect(48, 120, 16, 9)],
    'alien_big_green': pygame.Rect(96, 0, 16, 16),
    'alien_big_red': pygame.Rect(112, 0, 16, 16),
    'alien_green': pygame.Rect(128, 0, 16, 16),
    'alien_red': pygame.Rect(144, 0, 16, 16),
    'plane_green': pygame.Rect(160, 0, 16, 16),
    'plane_red': pygame.Rect(176, 0, 16, 16),
    'smartbomb_green': pygame.Rect(192, 0, 5, 5),
    'smartbomb_red': pygame.Rect(200, 0, 5, 5),
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
                pygame.Rect(176, 56, 8, 8), pygame.Rect(184, 56, 8, 8)],
    'red': pygame.Rect(0, 64, 8, 8),
    'green': pygame.Rect(8, 64, 8, 8),
    'blue': pygame.Rect(16, 64, 8, 8),
    'cyan': pygame.Rect(24, 64, 8, 8),
    'magenta': pygame.Rect(32, 64, 8, 8),
    'yellow': pygame.Rect(40, 64, 8, 8),
}

CHAR_MAP = {' ': 42,
            'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
            'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P':
            15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22,
            'X': 23, 'Y': 24, 'Z': 25, '0': 26, '1': 27, '2': 28, '3': 29,
            '4': 30, '5': 31, '6': 32, '7': 33, '8': 34, '9': 35, '↑': 36,
            '↓': 37, '←': 38, '→': 39, '©': 40, 'popy': 41, '.': 43,
            ',': 44, '!': 45, ':': 46, ';': 47, 'x': 48}


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
#
# NOTE: The original values are hard AF.  Factor added to tone it

DIFFICULTY = 0.75

240 / 6
WAVES = [
    (12, DIFFICULTY * 60 / (1 + 4.8125), 990),
    (15, DIFFICULTY * 60 / (1 + 2.875), 990),
    (18, DIFFICULTY * 60 / (1 + 1.75), 990),
    (12, DIFFICULTY * 60 / (1 + 1.03), 990),
    (16, DIFFICULTY * 60 / (1 + 0.625), 990),
    (14, DIFFICULTY * 60 / (1 + 0.375), 991),
    (17, DIFFICULTY * 60 / (1 + 0.25), 991),
    (10, DIFFICULTY * 60 / (1 + 0.125), 992),
    (13, DIFFICULTY * 60 / (1 + 0.0625), 993),
    (16, DIFFICULTY * 60 / (1 + 0.04), 994),
    (19, DIFFICULTY * 60 / (1 + 0.02), 994),
    (12, DIFFICULTY * 60 / (1 + 0.016), 995),
    (14, DIFFICULTY * 60 / (1 + 0.008), 995),
    (16, DIFFICULTY * 60 / (1 + 0.004), 996),
    (18, DIFFICULTY * 60 / (1 + 0), 996),
    (14, DIFFICULTY * 60 / (1 + 0), 997),
    (17, DIFFICULTY * 60 / (1 + 0), 997),
    (19, DIFFICULTY * 60 / (1 + 0), 997),
    (22, DIFFICULTY * 60 / (1 + 0), 997),
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

# Screen height is 240, row 0 is at the bottom in the arcade
FORK_HEIGHT_RANGE = (240 - 159, 240 - 128)
INCOMING_REQUIRED_HEIGHT = 240 - 200
INCOMING_SLOTS = 8
MAX_LAUNCHES_PER_FRAME = 4
MISSILE_SPLITS = 3
PLANE_SPEED = 20
SATELLITE_SPEED = 30
MAX_SMARTBOMBS_ON_SCREEN = 3
LOW_AMMO_WARN_THRESHOLD = 3

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

class MessageConfig(NamedTuple):
    text: str
    pos: Point
    anchor: str
    color: ColorLike = 'white'
    scale: tuple[float, float] = (1, 1)


MESSAGES = {
    'briefing': {
        'CITIES': MessageConfig('CITIES', GRID(21, 18, 2, 2).center, 'center', COLOR.normal_text),  # noqa: E501
        'DEFEND': MessageConfig('DEFEND', GRID(9, 18, 2, 2).center, 'center', COLOR.normal_text),  # noqa: E501
        'MULT': MessageConfig('1         ', GRID(15, 11, 2, 2).center, 'center', COLOR.special_text),
        'PLAYER': MessageConfig('PLAYER  ', GRID(15, 8, 2, 2).center, 'center', COLOR.normal_text),
        'PLAYER_NO': MessageConfig('       1', GRID(15, 8, 2, 2).center, 'center', COLOR.special_text),
        'x POINTS': MessageConfig('  x POINTS', GRID(15, 11, 2, 2).center, 'center', COLOR.normal_text),
        '↓ DEFEND': MessageConfig('↓', GRID(9, 19, 2, 2).center, 'center', COLOR.special_text),
        '↓ CITIES': MessageConfig('↓', GRID(21, 19, 2, 2).center, 'center', COLOR.special_text),
    },
    'debriefing': {
        'BONUS POINTS': MessageConfig('BONUS POINTS', GRID(15, 8, 2, 1).center, 'center', COLOR.normal_text),
    },
    'game': {
        'SCORE': MessageConfig('SCORE', GRID(8, 0, 2, 1).midright, 'midright', COLOR.special_text),
        'HIGHSCORE': MessageConfig('HIGHSCORE', GRID(15, 0, 2, 1).center, 'center', COLOR.special_text),
        'BONUS CITIES': MessageConfig(' x ', GRID(22, 0, 1, 1).midleft, 'midleft', COLOR.special_text)
    },
    'highscore entry': {
        'PLAYER  ': MessageConfig('PLAYER  ', GRID(15, 7, 2, 1).center, 'center', COLOR.normal_text),
        'GREAT SCORE': MessageConfig('GREAT SCORE', GRID(15, 9, 2, 2).center, 'center', COLOR.normal_text, (2, 1)),
        'ENTER YOUR INITIALS': MessageConfig('ENTER YOUR INITIALS', GRID(15, 12, 2, 1).center, 'center', COLOR.normal_text),
        'SPIN BALL TO CHANGE LETTER': MessageConfig('SPIN BALL TO CHANGE LETTER', GRID(15, 14, 2, 1).center, 'center', COLOR.normal_text),
        'PRESS ANY FIRE SWITCH TO SELECT': MessageConfig('PRESS ANY FIRE SWITCH TO SELECT', GRID(15, 16, 2, 1).center, 'center', COLOR.normal_text),
    },
    'highscores': {
        'BONUS CITY EVERY POINTS': MessageConfig('BONUS CITY EVERY       POINTS', GRID(15, 15, 2, 1).center, 'center', COLOR.normal_text),
        'BONUS CITY POINTS': MessageConfig('                 10000       ', GRID(15, 15, 2, 1).center, 'center', COLOR.special_text),
        'HIGH SCORES': MessageConfig('HIGH SCORES', GRID(15, 2, 2, 1).center, 'center', COLOR.normal_text),
    },
    'pause': {
        'PAUSE': MessageConfig('PAUSE', GRID(15, 4, 2, 2).center, 'center', COLOR.normal_text, (3, 3)),
    },
    'title': {
        'MISSILE': MessageConfig('MISSILE', GRID(GRID_WIDTH / 2, GRID_HEIGHT / 2 - 1, 1, 1).midbottom, 'midbottom', COLOR.title, (3, 3)),
        'COMMAND': MessageConfig('COMMAND', GRID(GRID_WIDTH / 2, GRID_HEIGHT / 2 + 1, 1, 1).midtop, 'midtop', COLOR.title, (3, 3)),
    },
}
