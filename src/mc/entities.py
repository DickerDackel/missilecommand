from random import shuffle, uniform

import pygame
import tinyecs as ecs

from pygame.typing import Point

from pgcooldown import LerpThing, Cooldown

import ddframework.cache as cache

import mc.config as C

from mc.components import AutoCycle, Comp, PRSA
from mc.sprite import TSprite, TAnimSprite
from mc.typing import EntityID, Trail


def mk_battery(battery_id: int, pos: Point) -> None:
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

    return (eid, missiles)

def mk_city(city_id, pos):
    textures = cache.get('cities')
    cd = Cooldown(10)
    cd.remaining = uniform(0, 10)

    eid = f'city-{city_id}'
    eid = ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_CITY)
    ecs.add_component(eid, Comp.ID, city_id)
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(cd, textures))
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))

    return eid

def mk_crosshair():
    eid = 'player'
    ecs.create_entity(eid)
    ecs.set_property(eid, Comp.WANTS_MOUSE)
    ecs.add_component(eid, Comp.TEXTURE, cache.get('crosshair'))
    ecs.add_component(eid, Comp.PRSA, PRSA())

    return eid

def mk_defense(pos: Point, target: EntityID, speed: float):
    textures = cache.get('missiles-heads')

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_DEFENSE)
    ecs.set_property(eid, Comp.IS_MISSILE)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))
    ecs.add_component(eid, Comp.TARGET, target)
    ecs.add_component(eid, Comp.SPEED, speed)
    ecs.add_component(eid, Comp.TRAIL, [(pos, pos)])

    return eid

def mk_explosion(pos):
    scale = LerpThing(0.1, 1, 0.5, repeat=2, loops=2)

    textures = cache.get('explosions').copy()
    shuffle(textures)
    texture_cycle = AutoCycle(0.5, textures)

    prsa = PRSA(pos, scale=0.1)

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_EXPLOSION)
    ecs.add_component(eid, Comp.PRSA, prsa)
    ecs.add_component(eid, Comp.TEXTURES, texture_cycle)
    ecs.add_component(eid, Comp.EXPLOSION_SCALE, scale)

def mk_silo(silo_id: int, battery_id: int, pos: Point) -> None:
    textures = cache.get('missiles')

    eid = f'silo-{silo_id}'
    ecs.create_entity(eid)
    ecs.set_property(eid, Comp.IS_SILO)
    ecs.add_component(eid, Comp.ID, silo_id)
    ecs.add_component(eid, Comp.BATTERY_ID, battery_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))

    return eid

def mk_target(pos: Point, parent: EntityID):
    textures = cache.get('targets')

    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_TARGET)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))

    return eid

def mk_textlabel(text: str, pos: Point, anchor: str,
                 color: pygame.Color, scale: tuple[float, float] = (1, 1),
                 eid: str | None = None) -> EntityID:
    eid = ecs.create_entity(eid)

    ecs.set_property(eid, Comp.IS_TEXT)
    ecs.add_component(eid, Comp.TEXT, text)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos, scale=scale))
    ecs.add_component(eid, Comp.ANCHOR, anchor)
    ecs.add_component(eid, Comp.COLOR, color)

    return eid

def mk_trail_eraser(trail: Trail) -> None:
    eid = ecs.create_entity()
    ecs.set_property(eid, Comp.IS_DEAD_TRAIL)
    ecs.add_component(eid, Comp.TRAIL, trail)

    return eid



########################################################################
#   ___  _     _ 
#  / _ \| | __| |
# | | | | |/ _` |
# | |_| | | (_| |
#  \___/|_|\__,_|
#                
########################################################################

def mk_missile(missile_id, silo_id, pos):
    textures = cache.get('missiles')
    sprite = TAnimSprite(pos, textures, delay=1)

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.IS_MISSILE, True)
    ecs.add_component(eid, Comp.ID, silo_id * len(C.SILO_OFFSETS))
    ecs.add_component(eid, Comp.SILO_ID, silo_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.SPRITE, sprite)

    return eid


def mk_ruin(ruin_id, pos):
    texture = cache.get('ruins')
    sprite = TSprite(pos, texture)

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.ID, ruin_id)
    ecs.add_component(eid, Comp.IS_RUIN, True)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.SPRITE, sprite)

    return eid
