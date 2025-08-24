import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from typing import Hashable

import pygame

from pygame.math import Vector2 as vec2
from pygame.typing import Point

Container = pygame.Rect
EntityID = Hashable
Momentum = vec2
Trail = list[tuple[Point, Point]]


class Prop(StrEnum):
    # Flags
    IS_BATTERY = auto()  # Batteries contain silos (unlaunched missiles)
    IS_CITY = auto()  # This is a city
    IS_DEAD = auto()  # This object is dead and will be culled by a system
    IS_DEAD_TRAIL = auto()  # FIXME, probably redundant?
    IS_DEAD_FLYER = auto()  # Flyer is dead but still rendered
    IS_DEFENSE = auto()  # opposite of IS_INCOMING
    IS_EXPLOSION = auto()  # Yeah...
    IS_FLYER = auto()  # Plane/Satellite thingy
    IS_GAMEOVER = auto()  # stuff added by the gameover state
    IS_INCOMING = auto()  # opposite of IS_DEFENSE
    IS_INFRASTRUCTURE = auto()  # mouse cursor, score, ...
    IS_MISSILE = auto()  # Missile head in flight
    IS_PLANE = auto()  # Flyer is a plane
    IS_RUIN = auto()  # Damaged city
    IS_SATELLITE = auto()  # Flyer is an alien
    IS_SILO = auto()  # Missile head not launched
    IS_TARGET = auto()  # Crosshair after mouse click
    IS_TEXT = auto()  # Any text label
    IS_TRAIL = auto()  # Line segments left by missiles


class Comp(StrEnum):
    # Immutables
    ANCHOR = auto()  # sys_draw_textlabel, sys_draw_texture
    BATTERY_ID = auto()  # To identify which battery a silo belongs to
    COLOR = auto()  # sys_draw_textlabel
    ID = auto()  # General id, always belongs to the entity
    WANTS_MOUSE = auto()  # sys_mouse, bool - for entities that want mouse position in prsa.pos

    # Actual objects
    COLOR_CYCLE = auto()
    CONTAINER = auto()  # Rect
    FLYER_SHOOT_COOLDOWN = auto()
    HITBOX = auto()
    LIFETIME = auto()  # Cooldown, sys_lifetime
    MASK = auto()  # sprite mask for collision checks
    MOMENTUM = auto()  # sys_momentum
    PRSA = auto()
    SCALE = auto()  # LerpThing, sys_apply_scale
    SHUTDOWN = auto()
    SOUND = auto()
    TARGET = auto()  # sys_target_reached - A target for a sprite or aiming
    TEXT = auto()  # sys_draw_textlabel - A text label for the sprite based font
    TEXT_LIST = auto()
    TEXT_SEQUENCE = auto()
    TEXTURE = auto()  # sys_draw_texture, sys_texture_from_texture_list - Exactly what it says
    TEXTURE_LIST = auto()  # sys_draw_texture - An AutoSequence for textures
    TRAIL = auto()  # sys_trail, sys_update_trail, sys_trail_eraser
