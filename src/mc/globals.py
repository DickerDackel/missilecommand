from importlib.resources import files
from types import SimpleNamespace

import pygame

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
    background='darkslategray',
    grid='grey',
)

########################################################################
#   ____                        ____       _   _   _                 
#  / ___| __ _ _ __ ___   ___  / ___|  ___| |_| |_(_)_ __   __ _ ___ 
# | |  _ / _` | '_ ` _ \ / _ \ \___ \ / _ \ __| __| | '_ \ / _` / __|
# | |_| | (_| | | | | | |  __/  ___) |  __/ |_| |_| | | | | (_| \__ \
#  \____|\__,_|_| |_| |_|\___| |____/ \___|\__|\__|_|_| |_|\__, |___/
#                                                          |___/     
########################################################################

POS_BATTERY_X_STEP = 8
POS_BATTERY_Y_STEP = 3
POS_BATTERY_LEFT =   (24, SCREEN.bottom - 8)
POS_BATTERY_CENTER = (SCREEN.centerx, SCREEN.bottom - 8)
POS_BATTERY_RIGHT =  (SCREEN.width - 24, SCREEN.bottom - 8)

POS_GROUND = SCREEN.midbottom
POS_CITY_1 = ( 56, SCREEN.bottom - 8)
POS_CITY_2 = ( 80, SCREEN.bottom - 6)
POS_CITY_3 = (104, SCREEN.bottom - 9)
POS_CITY_4 = (154, SCREEN.bottom - 9)
POS_CITY_5 = (180, SCREEN.bottom - 6)
POS_CITY_6 = (206, SCREEN.bottom - 8)

########################################################################
#  ____             _ _            
# / ___| _ __  _ __(_) |_ ___  ___ 
# \___ \| '_ \| '__| | __/ _ \/ __|
#  ___) | |_) | |  | | ||  __/\__ \
# |____/| .__/|_|  |_|\__\___||___/
#       |_|                        
########################################################################

SPRITESHEET_CROSSHAIR = pygame.Rect(0, 0, 7, 7)
SPRITESHEET_TARGET = pygame.Rect(8, 0, 7, 7)
SPRITESHEET_MISSILE = pygame.Rect(16, 0, 4, 3)

SPRITESHEET_BIG_CITY = pygame.Rect(32, 0, 32, 16)
SPRITESHEET_CITY = pygame.Rect(64, 0, 32, 16)
SPRITESHEET_ALIEN_BIG_GREEN = pygame.Rect(96, 0, 16, 16)
SPRITESHEET_ALIEN_BIG_RED = pygame.Rect(112, 0, 16, 16)
SPRITESHEET_ALIEN_GREEN = pygame.Rect(128, 0, 16, 16)
SPRITESHEET_ALIEN_RED = pygame.Rect(144, 0, 16, 16)
SPRITESHEET_PLANE_GREEN = pygame.Rect(160, 0, 16, 16)
SPRITESHEET_PLANE_RED = pygame.Rect(176, 0, 16, 16)
SPRITESHEET_SMARTBOMB_GREEN = pygame.Rect(192, 0, 16, 16)
SPRITESHEET_SMARTBOMB_RED = pygame.Rect(200, 0, 16, 16)
SPRITESHEET_GROUND = pygame.Rect(0, 16, 256, 32)
