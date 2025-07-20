from random import choice, uniform

import pygame
import tinyecs as ecs

from pygame.typing import Point

from pgcooldown import LerpThing, Cooldown
from pygame import Vector2

import ddframework.cache as cache

import mc.config as C

from mc.components import AutoCycle, Comp, PRSA
from mc.sprite import TSprite, TAnimSprite
from mc.typing import EntityID, Trail
from mc.utils import colorize


def mk_crosshair():
    eid = 'player'
    ecs.create_entity(eid)
    ecs.add_component(eid, Comp.TEXTURE, cache.get('crosshair'))
    ecs.add_component(eid, Comp.PRSA, PRSA())
    ecs.add_component(eid, Comp.WANTS_MOUSE, True)

    return eid


def mk_city(city_id, pos):
    textures = cache.get('cities')
    cd = Cooldown(10)
    cd.remaining = uniform(0, 10)

    eid = f'city-{city_id}'
    eid = ecs.create_entity(eid)
    ecs.add_component(eid, Comp.IS_CITY, True)
    ecs.add_component(eid, Comp.ID, city_id)
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(cd, textures))
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))

    return eid


def mk_battery(battery_id: int, pos: Point) -> None:
    rect = pygame.Rect(0, 0, 10, 10).move_to(center=pos)

    eid = f'battery-{battery_id}'
    ecs.create_entity(eid)
    ecs.add_component(eid, Comp.IS_BATTERY, True)
    ecs.add_component(eid, Comp.ID, battery_id)
    ecs.add_component(eid, Comp.RECT, rect)

    no_missiles = len(C.SILO_OFFSETS)
    missiles = [mk_silo(battery_id * no_missiles + i,
                        battery_id,
                        pos + C.BATTERY_SILO_OFFSET + offset)
                for i, offset in enumerate(C.SILO_OFFSETS)]

    return (eid, missiles)

def mk_silo(silo_id: int, battery_id: int, pos: Point) -> None:
    textures = cache.get('missiles')

    eid = f'silo-{silo_id}'
    ecs.create_entity(eid)
    ecs.add_component(eid, Comp.IS_SILO, True)
    ecs.add_component(eid, Comp.ID, silo_id)
    ecs.add_component(eid, Comp.BATTERY_ID, battery_id)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))

    return eid

def mk_target(pos: Point, parent: EntityID):
    textures = cache.get('targets')

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.IS_TARGET, True)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))

    return eid

def mk_defense(pos: Point, target: EntityID, speed: float):
    textures = cache.get('missiles-heads')

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.IS_DEFENSE, True)
    ecs.add_component(eid, Comp.IS_MISSILE,True)
    ecs.add_component(eid, Comp.PRSA, PRSA(pos))
    ecs.add_component(eid, Comp.TEXTURES, AutoCycle(1, textures))
    ecs.add_component(eid, Comp.TARGET, target)
    ecs.add_component(eid, Comp.SPEED, speed)
    ecs.add_component(eid, Comp.TRAIL, [(pos, pos)])

    return eid

def mk_trail_eraser(trail: Trail) -> None:
    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.IS_DEAD_TRAIL, True)
    ecs.add_component(eid, Comp.TRAIL, trail)

    return eid

# def mk_explosion(pos):
#     radiuses = [(0.1, 1, 0.5), (1, 0.1, 0.5)]
#     textures = cache.get('explosions')

#     eid = ecs.create_entity()
#     ecs.add_component(eid, Comp.IS_EXPLOSION, True)
#     ecs.add_component(eid, Comp.PRSA, PRSA(pos))





def mk_missile(missile_id, silo_id, pos):
    textures = cache.get('missiles')
    sprite = TAnimSprite(pos, textures, delay=1)

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.ID, silo_id * len(C.SILO_OFFSETS))
    ecs.add_component(eid, Comp.SILO_ID, silo_id)
    ecs.add_component(eid, Comp.IS_MISSILE, True)
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


class Trail:
    def __init__(self, start, parent, renderer, trail_texture):

        self.trail = []

    def update(self, dt):
        ppos = self.parent.pos.copy()
        self.trail.append((self.start, ppos))
        self.start = ppos

    def draw(self):
        if not self.trail: return

        bkp_target = self.renderer.target
        bkp_color = self.renderer.draw_color

        self.renderer.target = self.trail_texture
        self.renderer.draw_color = C.COLOR.enemy_missile
        self.renderer.draw_line(*self.trail[-1])

        self.renderer.target = bkp_target
        self.renderer.draw_color = bkp_color

    def kill(self):
        bkp_target = self.renderer.target
        bkp_color = self.renderer.draw_color

        self.renderer.target = self.trail_texture
        self.renderer.draw_color = C.COLOR.clear
        for t in self.trail:
            self.renderer.draw_line(*t)

        self.renderer.draw_color = bkp_color
        self.renderer.target = bkp_target

        self.target = None


def mk_explosion(pos):
    ramp = ((0.1, 1, 0.5), (1, 0.1, 0.5))

    textures = cache.get('explosions')
    sprite = TSprite(pos, texture)

    eid = ecs.create_entity()
    ecs.add_component(eid, Comp.IS_EXPLOSION, True)
    ecs.add_component(eid, Comp.POS, pos)




class Explosion(TSprite):
    @staticmethod
    def collidepoint(left, right):
        v = left.pos - right.pos

        scale = left.scale if isinstance(left, Explosion) else right.scale
        radius = 16 * scale

        return v.length() < radius

    def __init__(self, pos):
        self.textures = cache.get('explosion')
        texture = choice(self.textures)
        super().__init__(pos, texture)

        self.lt_cfg = iter(self.RAMP)
        self.lt = LerpThing(*next(self.lt_cfg), repeat=0)
        self.scale = self.lt()

        self.color_change = Cooldown(0.1)

    def update(self, dt):
        self.scale = self.lt()

        if self.lt.finished():
            try:
                self.lt = LerpThing(*next(self.lt_cfg), repeat=0)
            except StopIteration:
                self.kill()

    def draw(self):
        if self.color_change.cold():
            self.color_change.reset()
            self.image = choice(self.textures)

        self.image.draw(dstrect=self.rect.scale_by(self.scale))


class TString:
    def __init__(self, pos, text, *, scale=1, anchor='center', color=None):
        self.pos = Vector2(pos)
        self.anchor = anchor

        font = cache.get('letters')

        def get_letter_texture(c):
            return colorize(font[C.CHAR_MAP[c]], color) if color else font[C.CHAR_MAP[c]]

        self.letters = [get_letter_texture(c) for c in text]

        self.rect_1 = self.letters[0].get_rect().scale_by(scale)
        self.rect = self.rect_1.scale_by(len(self.letters), 1)
        self.update(0)

    def update(self, dt):
        setattr(self.rect, self.anchor, self.pos)

    def draw(self):
        rect = self.rect_1.copy().move_to(topleft=self.rect.topleft)
        step = rect.width
        for c in self.letters:
            c.draw(dstrect=rect)
            rect.move_ip(step, 0)
