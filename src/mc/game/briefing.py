import pygame._sdl2 as sdl2

from ddframework.app import StateExit
from pgcooldown import Cooldown
from ddframework.app import GameState

import mc.globals as G


class Prep(GameState):
    def __init__(self, app):
        self.app = app
        self.cooldown = Cooldown(3)

        surf = G.FONT.normal.render('LOREM IPSUM', 'red', True)
        self.texture = sdl2.Texture.from_surface(self.app.renderer, surf)
        self.rect = surf.get_rect(center=app.logical_rect.center)


    def update(self, dt):
        if self.cooldown.cold():
            raise StateExit(-1)

    def draw(self):
        self.texture.draw(dstrect=self.rect)
