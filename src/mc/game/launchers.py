import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Callable
from random import choice, randint, random, shuffle

import pygame
import tinyecs as ecs

from pygame.math import Vector2 as vec2
from pygame.typing import Point

from pgcooldown import Cooldown, LerpThing

from ddframework.cache import cache as cache
from ddframework.dynamicsprite import PRSA
from ddframework.autosequence import AutoSequence

import mc.config as C

from mc.game.types import Comp, EIDs
from mc.types import Container, EntityID, Momentum, Trail


def mk_battery(battery_id: int, pos: Point) -> tuple[EntityID, list[EntityID]]:
    """Creates a battery of missile silos

    Arguments:
        battery_id -> The index of the battery (0, 1, 2)
        pos: The placement of the battery

    Returns:
        entitiy IDs  for 15 silos in total
    """

    rect = pygame.Rect(0, 0, 10, 10).move_to(center=pos)

    eid = f'battery-{battery_id}'
    ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_BATTERY)
    ecs.add_component(eid, Comp.ID, battery_id)
    ecs.add_component(eid, Comp.RECT, rect)

    no_missiles = len(C.SILO_OFFSETS)
    missiles = [mk_silo(battery_id * no_missiles + i,
                        battery_id,
                        pos + C.BATTERY_SILO_OFFSET + offset)
                for i, offset in enumerate(C.SILO_OFFSETS)]

    return missiles


def mk_city(city_id: int, pos: Point) -> EntityID:
    textures = cache['cities']
    auto_sequence = AutoSequence(textures, 10)
    auto_sequence.lt.duration.normalized = random()  # ty: ignore[invalid-assignment]

    eid = f'city-{city_id}'
    eid = ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_CITY)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))

    return eid


def mk_ruin(city_id: int, pos: Point) -> EntityID:
    textures = cache['ruins']
    auto_sequence = AutoSequence(textures, 10)
    auto_sequence.lt.duration.normalized = random()  # ty: ignore[invalid-assignment]

    eid = f'city-{city_id}'
    eid = ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_RUIN)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))


def mk_crosshair() -> EntityID:
    eid = 'player'
    ecs.create_entity(eid)
    ecs.set_property(eid, Comp.WANTS_MOUSE)
    ecs.add_component(eid, Comp.TEXTURE, cache['crosshair'])
    ecs.add_component(eid, Comp.PRSA, PRSA())

    return eid


def mk_defense(pos: Point, target: EntityID, speed: float) -> EntityID:
    textures = cache['missiles-heads']
    auto_sequence = AutoSequence(textures, 1)

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_DEFENSE)
    ecs.set_property(eid, Comp.IS_MISSILE)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.TARGET, target)
    ecs.add_component(eid, Comp.SPEED, speed)
    ecs.add_component(eid, Comp.TRAIL, [(pos, pos)])

    return eid


def mk_explosion(pos: Point) -> EntityID:
    scale = LerpThing(0.1, 1, 0.5, repeat=2, loops=2)

    textures = cache['explosions'].copy()
    shuffle(textures)
    auto_sequence = AutoSequence(textures, 0.5)

    prsa = PRSA(vec2(pos), scale=0.1)

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_EXPLOSION)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.EXPLOSION_SCALE, scale)

    return eid


def mk_flyer(min_height: float, max_height: float, fire_cooldown: float,
             container: Container, shutdown_callback: Callable) -> EntityID:
    kind = choice(('alien', 'plane'))
    color = choice(('red', 'green'))
    texture = cache[f'{kind}_{color}']
    speed = C.PLANE_SPEED if kind == 'plane' else C.SATELLITE_SPEED
    height = randint(max_height, min_height)

    prsa = PRSA(pos=vec2(-16, height))
    eid = ecs.create_entity(EIDs.FLYER)
    ecs.set_property(eid, Comp.IS_FLYER)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.TEXTURE, texture)
    ecs.add_component(eid, Comp.FLYER_FIRE_COOLDOWN, Cooldown(fire_cooldown))
    ecs.add_component(eid, Comp.MOMENTUM, Momentum(speed, 0))
    ecs.add_component(eid, Comp.CONTAINER, container)
    ecs.add_component(eid, Comp.NOTIFY_DEAD, shutdown_callback)

    return eid


def mk_missile(start: vec2, dest: vec2, speed: float,
               shutdown_callback: Callable | None = None,
               *, incoming: bool) -> None:
    textures = cache['missile-heads']
    auto_sequence = AutoSequence(textures, 1)
    trail = [(start, start)]

    try:
        momentum = (dest - start).normalize() * speed
    except ValueError:
        momentum = vec2()

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_MISSILE)
    ecs.set_property(eid, Comp.IS_TRAIL)
    ecs.set_property(eid, Comp.IS_INCOMING if incoming else Comp.IS_DEFENSE)
    ecs.add_component(eid, Comp.PRSA, PRSA(start.copy()))
    ecs.add_component(eid, Comp.MOMENTUM, momentum)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.TARGET, dest.copy())
    ecs.add_component(eid, Comp.TRAIL, trail)
    if shutdown_callback is not None:
        ecs.add_component(eid, Comp.SHUTDOWN, shutdown_callback)

    return eid


def mk_silo(silo_id: int, battery_id: int, pos: Point) -> EntityID:
    textures = cache['missiles']
    auto_sequence = AutoSequence(textures, 1)

    eid = f'silo-{silo_id}'
    ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_SILO)
    ecs.add_component(eid, Comp.ID, silo_id)
    ecs.add_component(eid, Comp.BATTERY_ID, battery_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid


def mk_target(eid: EntityID, pos: Point) -> EntityID:
    textures = cache['targets']
    auto_sequence = AutoSequence(textures, 1)

    ecs.set_property(eid, Comp.IS_TARGET)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid


def mk_trail_eraser(trail: Trail) -> None:
    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_DEAD_TRAIL)
    ecs.add_component(eid, Comp.TRAIL, trail)


########################################################################
#   ___  _     _
#  / _ \| | __| |
# | | | | |/ _` |
# | |_| | | (_| |
#  \___/|_|\__,_|
#
########################################################################


def mk_ruin(ruin_id: int, pos: Point) -> EntityID:
    textures = cache['ruins']
    auto_sequence = AutoSequence(textures, 10)
    auto_sequence.lt.duration.normalized = random()  # ty: ignore[invalid-assignment]

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_RUIN)
    ecs.add_component(eid, Comp.ID, ruin_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid
