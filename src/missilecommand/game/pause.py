from itertools import cycle

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from pgcooldown import Cooldown

import missilecommand.config as C

from missilecommand.launchers import mk_textlabel
from missilecommand.types import Comp


class Pause(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

        self.labels = []

        msg = C.MESSAGES['pause']['PAUSE']
        eid = mk_textlabel(*msg, eid=msg.text)
        self.labels.append(eid)

        self.blink_cooldown = Cooldown(1)
        self.blink_colors = cycle(['red', 'blue'])

    def dispatch_event(self, e: pygame.event.Event) -> None:
        # NOTE: Pause is a stacked state that falls back to the main game and
        # does not exit to the desktop.
        if e.type == pygame.KEYDOWN and e.key in {pygame.K_p, pygame.K_ESCAPE}:
            self.teardown()
            raise StateExit(-1)

    def update(self, dt: float) -> None:
        if self.blink_cooldown.cold():
            for eid in self.labels:
                ecs.add_component(eid, Comp.COLOR, next(self.blink_colors))
            self.blink_cooldown.reset()

    def draw(self) -> None:
        # Done from the ECS in the underlying game state
        pass

    def teardown(self):
        for eid in self.labels:
            ecs.remove_entity(eid)
