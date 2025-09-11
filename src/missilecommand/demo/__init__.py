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
from missilecommand.utils import check_for_exit
from missilecommand.types import Comp


class Demo(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app

        self.state_label = None
        self.cd_state = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()
        self.state_label = mk_textlabel(
            'DEMO',
            self.app.logical_rect.center,
            'center', 'white', scale=2)

        self.cd_state = Cooldown(5)

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
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
        ecs.remove_entity(self.state_label)
        raise StateExit
