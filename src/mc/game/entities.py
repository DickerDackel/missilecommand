from random import choice

import pygame
import tinyecs as ecs

from pgcooldown import LerpThing, Cooldown
from pygame import Vector2

import ddframework.cache as cache

import mc.globals as G
from mc.sprite import TSprite, TAnimSprite
from mc.utils import to_viewport, colorize
from mc.components import Comp


def mk_crosshair():
    texture = cache.get('crosshair')
    rect = texture.get_rect()

    eid = 'player'
    ecs.create_entity(eid)
    ecs.add_component(eid, Comp.POS, Vector2())
    ecs.add_component(eid, Comp.WANTS_MOUSE, True)
    ecs.add_component(eid, Comp.TEXTURE, texture)
    ecs.add_component(eid, Comp.RECT, rect)


class Silo:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)

        textures = cache.get('missiles')
        self.missiles = [TAnimSprite(self.pos + offset, textures, delay=1)
                         for offset in G.MISSILE_OFFSETS]

    def draw(self):
        for m in self.missiles: m.draw()


class City(TSprite):
    def __init__(self, pos):
        self.textures = [cache.get('city'), cache.get('ruins')]
        super().__init__(pos, self.textures[0], anchor='midbottom')
        self.ruined = False

    def draw(self):
        self.image = self.textures[self.ruined]
        super().draw()


class Target(TAnimSprite):
    def __init__(self, pos, parent):
        textures = cache.get('targets')
        super().__init__(pos, textures, delay=0.3)
        self.parent = parent

class MissileHead(TAnimSprite):
    def __init__(self, start, target, speed):
        textures = cache.get('missile-heads')
        super().__init__(start, textures, delay=0.3, anchor='topleft')

        self.target = Vector2(target)
        self.speed = speed
        self.explode = False

    def update(self, dt):
        distance = self.target - self.pos
        speed = self.speed * dt

        if distance.length() <= speed:
            step = distance
            self.explode = True
        else:
            step = distance.normalize() * speed

        self.pos += step

        super().update(dt)

    def draw(self, renderer):
        super().draw()
        # bkp_color = renderer.draw_color
        # renderer.draw_color = 'yellow'
        # renderer.draw_point(self.pos)
        # renderer.draw_color = bkp_color

class Trail:
    def __init__(self, start, parent, renderer, trail_texture):
        self.start = Vector2(start)
        self.parent = parent
        self.renderer = renderer
        self.trail_texture = trail_texture

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
        self.renderer.draw_color = G.COLOR.enemy_missile
        self.renderer.draw_line(*self.trail[-1])

        self.renderer.target = bkp_target
        self.renderer.draw_color = bkp_color

    def kill(self):
        bkp_target = self.renderer.target
        bkp_color = self.renderer.draw_color

        self.renderer.target = self.trail_texture
        self.renderer.draw_color = G.COLOR.clear
        for t in self.trail:
            self.renderer.draw_line(*t)

        self.renderer.draw_color = bkp_color
        self.renderer.target = bkp_target

        self.target = None

class Mouse(TSprite):
    def __init__(self, window_rect, logical_rect):
        self.window_rect = window_rect
        self.logical_rect = logical_rect

        super().__init__(self.virtual_mouse_pos(), cache.get('crosshair'))

    def update(self, dt):
        self.pos = self.virtual_mouse_pos()
        super().update(dt)

    def virtual_mouse_pos(self):
        return  to_viewport(pygame.mouse.get_pos(),
                            self.window_rect.size,
                            self.logical_rect.size)

class Explosion(TSprite):
    RAMP = ((0.1, 1, 0.5), (1, 0.1, 0.5))

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
            return colorize(font[G.CHAR_MAP[c]], color) if color else font[G.CHAR_MAP[c]]

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
