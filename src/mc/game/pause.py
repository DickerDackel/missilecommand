from itertools import cycle

import pygame
import tinyecs as ecs

from ddframework.app import GameState, StateExit
from ddframework.gridlayout import GridLayout
from pgcooldown import Cooldown

import mc.config as C

from mc.components import Comp
from mc.entities import mk_textlabel


class Pause(GameState):
    def __init__(self, app):
        self.app = app

        self.labels = []

        msg = C.MESSAGES['PAUSE']
        eid = mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, msg.scale, eid=msg.text)
        self.labels.append(eid)

        self.blink_cooldown = Cooldown(1)
        self.blink_colors = cycle(['red', 'blue'])

    def dispatch_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in [pygame.K_p, pygame.K_ESCAPE]:
            print(f'killing {self.labels}')
            for eid in self.labels:
                ecs.remove_entity(eid)
            raise StateExit(-1)

    def update(self, dt):
        if self.blink_cooldown.cold():
            for eid in self.labels:
                ecs.add_component(eid, Comp.COLOR, next(self.blink_colors))
            self.blink_cooldown.reset()

    def draw(self):
        # Done from the ECS in the underlying game state
        pass
