import logging
logging.info(__name__)  # noqa: E402

from typing import Any

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown
from ddframework.app import App, GameState, StateExit

import missilecommand.config as C

from missilecommand.launchers import mk_textlabel
from missilecommand.systems import sys_draw_textlabel
from missilecommand.types import Comp
from missilecommand.utils import check_for_exit


class Title(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app

        self.entities = None
        self.cd_state = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        self.entities = []

        msg = C.MESSAGES['title']['MISSILE']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['title']['COMMAND']
        self.entities.append(mk_textlabel(*msg))

        self.cd_state = Cooldown(5)

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        elif e.type == pygame.KEYDOWN:
            elif e.key == pygame.K_1:
        check_for_exit(e)

                raise StateExit(1)

    def update(self, dt: float) -> None:
        if self.cd_state.cold():
            self.teardown()

    def draw(self) -> None:
        self.app.renderer.draw_color = C.COLOR.background
        self.app.renderer.clear()
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def teardown(self) -> None:
        ecs.reset()
        raise StateExit
