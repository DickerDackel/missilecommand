import pygame

from ddframework.app import StateExit
from pgcooldown import Cooldown
from ddframework.app import GameState

import mc.config as C

from mc.game.entities import TString


class Briefing(GameState):
    def __init__(self, app, mult):
        self.app = app
        self.cd = Cooldown(3)

        self.texts = {
            'PLAYER': TString(C.MESSAGES['PLAYER'][0], 'PLAYER ', anchor='midleft', color='blue'),
            'DEFEND': TString(C.MESSAGES['DEFEND CITIES'][0], 'DEFEND      CITIES', anchor='midleft', color='blue'),
            'x POINTS': TString(C.MESSAGES['x POINTS'][0], 'x POINTS', anchor='midleft', color='blue'),
            'MULT': TString((0, 0), '1 ', color='red'),
            'PLAYER_NO': TString((0, 0), '1', color='red')
        }
        self.texts['MULT'].rect.midright = self.texts['x POINTS'].rect.midleft
        self.texts['PLAYER_NO'].rect.midleft = self.texts['PLAYER'].rect.midright

        self.cd = Cooldown(3)

    def dispatch_events(self, e):
        if e.key == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            raise StateExit(None)

    def update(self, dt):
        if self.cd.cold():
            raise StateExit(None)

    def draw(self):
        for t in self.texts.values():
            t.draw()
