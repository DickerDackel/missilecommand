import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Callable
from random import choice, randint, random, shuffle
from typing import Any

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pygame.math import Vector2 as vec2
from pygame.typing import ColorLike, Point

from pgcooldown import Cooldown, LerpThing

from ddframework.cache import cache as cache
from ddframework.dynamicsprite import PRSA
from ddframework.autosequence import AutoSequence
from rpeasings import out_quad

import mc.config as C

from mc.types import Comp, Container, EntityID, Momentum, Prop, Trail
from mc.utils import play_sound


def mk_battery(battery_id: int, pos: Point) -> tuple[EntityID, list[EntityID]]:
    """Creates a battery of missile silos

    Arguments:
        battery_id -> The index of the battery (0, 1, 2)
        pos: The placement of the battery

    Returns:
        list[EntityID] containing all silos
    """

    rect = pygame.Rect(0, 0, 10, 10).move_to(center=pos)

    eid = f'battery-{battery_id}'
    ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_BATTERY)
    ecs.add_component(eid, Comp.ID, battery_id)
    ecs.add_component(eid, Comp.HITBOX, rect)

    no_silos = len(C.SILO_OFFSETS)
    silos = [mk_silo(battery_id * no_silos + i,
                     battery_id,
                     pos + C.BATTERY_SILO_OFFSET + offset)
             for i, offset in enumerate(C.SILO_OFFSETS)]

    return silos


def mk_city(city_id: int, pos: Point) -> EntityID:
    """Create a city entity"""
    textures = cache['textures']['small-cities']
    auto_sequence = AutoSequence(textures, 10)
    auto_sequence.lt.duration.normalized = random()  # ty: ignore[invalid-assignment]

    eid = city_id
    eid = ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_CITY)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid


def mk_crosshair() -> EntityID:
    eid = 'player'
    pos = vec2(pygame.mouse.get_pos())
    ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_INFRASTRUCTURE)
    ecs.set_property(eid, Comp.WANTS_MOUSE)
    ecs.add_component(eid, Comp.TEXTURE, cache['textures']['crosshair'])
    ecs.add_component(eid, Comp.PRSA, PRSA(pos=pos))

    return eid


def mk_explosion(pos: Point) -> EntityID:
    scale = LerpThing(0.1, 1, C.EXPLOSION_DURATION, repeat=2, loops=2)

    textures = cache['textures']['explosions'].copy()
    mask = cache['masks']['explosions'][0]

    shuffle(textures)
    auto_sequence = AutoSequence(textures, C.EXPLOSION_DURATION)

    prsa = PRSA(vec2(pos), scale=0.1)

    eid = ecs.create_entity()
    ecs.set_property(eid, Prop.IS_EXPLOSION)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.SCALE, scale)
    ecs.add_component(eid, Comp.MASK, mask)

    return eid


def mk_flyer(eid: EntityID, min_height: float, max_height: float, fire_cooldown: float,
             container: Container, shutdown_callback: Callable) -> EntityID:
    kind = choice(('alien', 'plane'))
    color = choice(('red', 'green'))
    texture = cache['textures'][f'{kind}_{color}']
    mask = cache['masks'][f'{kind}_{color}']
    speed = C.PLANE_SPEED if kind == 'plane' else C.SATELLITE_SPEED
    height = randint(max_height, min_height)
    sound = play_sound(cache['sounds']['flyer'], loops=-1)

    def stop_sound(eid):
        sound.stop()

    shutdown = (shutdown_callback, stop_sound)

    prsa = PRSA(pos=vec2(-16, height))
    ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_FLYER)
    ecs.set_property(eid, Prop.IS_PLANE if kind == 'plane' else Prop.IS_SATELLITE)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.TEXTURE, texture)
    ecs.add_component(eid, Comp.MASK, mask)
    ecs.add_component(eid, Comp.FLYER_FIRE_COOLDOWN, Cooldown(fire_cooldown))
    ecs.add_component(eid, Comp.MOMENTUM, Momentum(speed, 0))
    ecs.add_component(eid, Comp.CONTAINER, container)
    ecs.add_component(eid, Comp.SHUTDOWN, shutdown)
    ecs.add_component(eid, Comp.SOUND, sound)

    return eid


def mk_gameover_explosion(pos: Point, scale: float, eid: EntityID) -> EntityID:
    texture = cache['textures']['gameover']
    prsa = PRSA(pos=vec2(pos))
    renderer = texture.renderer
    scl = renderer.logical_size[1] / C.SPRITESHEET['gameover'].height
    scale = LerpThing(0.1, scl, 1.5, repeat=0, ease=out_quad)
    colors = AutoSequence(C.EXPLOSION_COLORS, 0.1, repeat=1)

    ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_EXPLOSION)
    ecs.add_component(eid, Comp.TEXTURE, texture)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.SCALE, scale)
    ecs.add_component(eid, Comp.COLOR_CYCLE, colors)

    return eid


def mk_gameover_text(the_end: AutoSequence, *args: Any, **kwargs: dict[str, Any]) -> EntityID:
    eid = mk_textlabel(*args, **kwargs)
    ecs.set_property(eid, Prop.IS_GAMEOVER)
    ecs.add_component(eid, Comp.TEXT_SEQUENCE, the_end)

    return eid


def mk_missile(start: vec2, dest: vec2, speed: float,
               shutdown_callback: Callable | None = None,
               *, incoming: bool) -> None:
    textures = cache['textures']['missile-heads']
    auto_sequence = AutoSequence(textures, 1)
    trail = [(start, start)]

    try:
        momentum = (dest - start).normalize() * speed
    except ValueError:
        momentum = vec2()

    eid = ecs.create_entity()
    ecs.set_property(eid, Prop.IS_MISSILE)
    ecs.set_property(eid, Prop.IS_TRAIL)
    ecs.set_property(eid, Prop.IS_INCOMING if incoming else Prop.IS_DEFENSE)
    ecs.add_component(eid, Comp.PRSA, PRSA(start.copy()))
    ecs.add_component(eid, Comp.MOMENTUM, momentum)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.TARGET, dest.copy())
    ecs.add_component(eid, Comp.TRAIL, trail)
    if shutdown_callback is not None:
        ecs.add_component(eid, Comp.SHUTDOWN, shutdown_callback)

    return eid


def mk_ruin(city_id: int, pos: Point) -> EntityID:
    textures = cache['textures']['small-ruins']
    auto_sequence = AutoSequence(textures, 3)
    auto_sequence.lt.duration.normalized = random()  # ty: ignore[invalid-assignment]

    eid = city_id
    eid = ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_RUIN)
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))


def mk_score_label(*args: Any, **kwargs: Any) -> EntityID:
    eid = mk_textlabel(*args, **kwargs)
    ecs.set_property(eid, Prop.IS_INFRASTRUCTURE)

    return eid


def mk_silo(silo_id: int, battery_id: int, pos: Point) -> EntityID:
    textures = cache['textures']['missiles']
    auto_sequence = AutoSequence(textures, 1)

    eid = f'silo-{silo_id}'
    ecs.create_entity(eid)
    ecs.set_property(eid, Prop.IS_SILO)
    ecs.add_component(eid, Comp.ID, silo_id)
    ecs.add_component(eid, Comp.BATTERY_ID, battery_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid


def mk_target(eid: EntityID, pos: Point) -> EntityID:
    textures = cache['textures']['targets']
    auto_sequence = AutoSequence(textures, 1)

    ecs.set_property(eid, Prop.IS_TARGET)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos)))
    ecs.add_component(eid, Comp.TEXTURE_LIST, auto_sequence)

    return eid


def mk_textlabel(text: str, pos: Point, anchor: str,
                 color: ColorLike, scale: tuple[float, float] = (1, 1),
                 eid: str | None = None) -> EntityID:
    eid = ecs.create_entity(eid)

    ecs.set_property(eid, Prop.IS_TEXT)
    ecs.add_component(eid, Comp.TEXT, text)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos), scale=scale))
    ecs.add_component(eid, Comp.ANCHOR, anchor)
    ecs.add_component(eid, Comp.COLOR, color)

    return eid


def mk_texture(texture: sdl2.Texture, pos: Point, anchor: str = 'center', color: ColorLike = None, eid: EntityID = None):
    eid = ecs.create_entity() if eid is None else ecs.create_entity(eid)

    ecs.add_component(eid, Comp.TEXTURE, texture)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos=vec2(pos)))
    ecs.add_component(eid, Comp.ANCHOR, anchor)
    if color is not None:
        ecs.add_component(eid, Comp.COLOR, color)

    return eid

def mk_trail_eraser(trail: Trail) -> None:
    eid = ecs.create_entity()
    ecs.set_property(eid, Prop.IS_DEAD_TRAIL)
    ecs.add_component(eid, Comp.TRAIL, trail)

    return eid
