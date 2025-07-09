import pygame

from ddframework.app import StateExit
from ddframework.app import GameState

from mc.game.entities import TString


class Pause(GameState):
    def __init__(self, app):
        self.app = app

        self.pause = TString(self.app.logical_rect.center,
                             'PAUSE', scale=3, color='blue')

    def dispatch_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
            raise StateExit()

    def update(self, dt):
        pass

    def draw(self):
        self.pause.draw()

