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
    'big_city': pygame.Rect(32, 0, 32, 16),
    'city': pygame.Rect(64, 0, 32, 16),
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
}

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
#  __  __
# |  \/  | ___  ___ ___  __ _  __ _  ___  ___
# | |\/| |/ _ \/ __/ __|/ _` |/ _` |/ _ \/ __|
# | |  | |  __/\__ \__ \ (_| | (_| |  __/\__ \
# |_|  |_|\___||___/___/\__,_|\__, |\___||___/
#                             |___/
########################################################################

MESSAGES = {
    'PLAYER': ((96, 144), (1, 1 )),
    'X POINTS': ((104, 112), (1, 1)),
    'DEFEND    CITIES': ((56, 56), (1, 1)),
}
