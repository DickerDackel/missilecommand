import pygame

from pygame import Vector2

import ddframework.cache as cache

import mc.globals as G
from mc.sprite import TSprite, TAnimSprite
from mc.utils import to_viewport


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
        texture = cache.get('city')
        super().__init__(pos, texture, anchor='midbottom')


class Target(TAnimSprite):
    def __init__(self, pos):
        textures = cache.get('targets')
        super().__init__(pos, textures, delay=0.3)

class MissileHead(TAnimSprite):
    def __init__(self, start, target, speed):
        textures = cache.get('missile-heads')
        super().__init__(start, textures, delay=0.3, anchor='topleft')

        self.target = Vector2(target)
        self.speed = speed
        self.explode = False
        print(self.speed)

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
