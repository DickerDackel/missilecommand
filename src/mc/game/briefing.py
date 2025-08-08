import logging
logging.info(__name__)  # noqa: E402

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from pgcooldown import Cooldown

import mc.config as C


class Briefing(GameState):
    def __init__(self, app: App, mult: float) -> None:
        self.app = app

        self.state_label = mk_textlabel('BRIEFING',
                                        self.app.logical_rect.topright,
                                        'topright', 'white', eid='briefingstate_label')

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

    def teardown(self) -> None:
        ecs.remove_entity(self.state_label)

        for t in self.labels:
            ecs.remove_entity(t)

    def dispatch_events(self, e: pygame.event.Event) -> None:
        if e.key == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.teardown()
            raise StateExit(-1)

    def update(self, dt: float) -> None:
        if self.cd.cold():
            self.teardown()
            raise StateExit(-1)

    def draw(self) -> None:
        ...  # FIXME
