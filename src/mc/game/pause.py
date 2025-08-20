import logging
logging.info(__name__)  # noqa: E402

from itertools import cycle

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from pgcooldown import Cooldown

import mc.config as C

from mc.launchers import mk_textlabel
from mc.types import Comp


class Pause(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

        # FIXME
        self.state_label = mk_textlabel('PAUSE',
                                        self.app.logical_rect.topright,
                                        'topright', 'white', eid='pausestate_label')

        self.labels = []

        msg = C.MESSAGES['pause']['PAUSE']
        eid = mk_textlabel(*msg, eid=msg.text)
        self.labels.append(eid)

        self.blink_cooldown = Cooldown(1)
        self.blink_colors = cycle(['red', 'blue'])

    def dispatch_event(self, e: pygame.event.Event) -> None:
        if e.type == pygame.KEYDOWN and e.key in {pygame.K_p, pygame.K_ESCAPE}:
            ecs.remove_entity(self.state_label)  # FIXME

            for eid in self.labels:
                ecs.remove_entity(eid)
            raise StateExit(-1)

    def update(self, dt: float) -> None:
        if self.blink_cooldown.cold():
            for eid in self.labels:
                ecs.add_component(eid, Comp.COLOR, next(self.blink_colors))
            self.blink_cooldown.reset()

    def draw(self) -> None:
        # Done from the ECS in the underlying game state
        pass
