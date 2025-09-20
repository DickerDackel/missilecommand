from typing import Any

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown
from ddframework.app import App, GameState, StateExit

import missilecommand.config as C

from missilecommand.launchers import mk_textlabel
from missilecommand.systems import (sys_draw_texture, sys_draw_textlabel, sys_textblink,
                                    sys_texture_from_texture_list)
from missilecommand.types import Comp
from missilecommand.utils import check_for_exit

THIS = 'highscores'


class Instructions(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        for msg in C.MESSAGES['instructions'].values():
            mk_textlabel(*msg)

        self.cd_state = Cooldown(15)

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        check_for_exit(e)

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                raise StateExit(1)
            elif e.key == pygame.K_f:
                self.app.window.fullscreen = not self.app.window.fullscreen

    def update(self, dt: float) -> None:
        if self.cd_state.cold():
            self.teardown()
            raise StateExit

    def draw(self) -> None:
        ecs.run_system(0, sys_textblink, Comp.COLOR_CYCLE)
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_texture_from_texture_list, Comp.TEXTURE_LIST)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self) -> None:
        pass
