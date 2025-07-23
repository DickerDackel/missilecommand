import pygame
import tinyecs as ecs

from ddframework.app import GameState
from ddframework.app import StateExit
from pgcooldown import Cooldown

import mc.config as C

from mc.entities import mk_textlabel


class Briefing(GameState):
    def __init__(self, app, mult):
        self.app = app
        self.cd = Cooldown(3)

        self.labels = []

        for t in ['PLAYER', 'DEFEND CITIES', 'x POINTS']:
            msg = C.MESSAGES[t]
            eid = mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid=msg.text)
            self.labels.append(eid)

        msg = C.MESSAGES['PLAYER_NO']
        mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid='PLAYER_NO')
        self.labels.append('PLAYER_NO')

        msg = C.MESSAGES['MULT']
        mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid='MULT')
        self.labels.append('MULT')

        self.cd = Cooldown(3)

    def teardown(self):
        for t in self.labels:
            ecs.remove_entity(t)

    def dispatch_events(self, e):
        if e.key == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.teardown()
            raise StateExit(None)

    def update(self, dt):
        if self.cd.cold():
            self.teardown()
            raise StateExit(None)

    def draw(self):
        ...  # FIXME
