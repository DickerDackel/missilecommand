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


class Splash(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app

        self.state_label = None
        self.cd_state = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()
        msg = C.MESSAGES['splash']['DACKELSOFT']
        mk_textlabel(*msg)

        self.cd_state = Cooldown(3)

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        check_for_exit(e)

    def update(self, dt: float) -> None:
        if self.cd_state.cold():
            self.teardown()
            raise StateExit

    def draw(self) -> None:
        # self.app.renderer.draw_color = C.COLOR.background
        # self.app.renderer.clear()
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def teardown(self) -> None:
        pass
