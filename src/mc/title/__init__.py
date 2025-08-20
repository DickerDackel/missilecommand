import logging
logging.info(__name__)  # noqa: E402

from typing import Any

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown
from ddframework.app import App, GameState, StateExit

import mc.config as C

from mc.launchers import mk_textlabel
from mc.systems import sys_textlabel
from mc.types import Comp


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
        if e.type == pygame.QUIT:
            raise StateExit(-1)
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                raise StateExit(-1)
            elif e.key == pygame.K_SPACE:
                self.teardown()
                raise StateExit
            elif e.key == pygame.K_1:
                raise StateExit(1)

    def update(self, dt: float) -> None:
        if self.cd_state.cold():
            self.teardown()

    def draw(self) -> None:
        self.app.renderer.draw_color = C.COLOR.background
        self.app.renderer.clear()
        ecs.run_system(0, sys_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def teardown(self) -> None:
        ecs.reset()
        raise StateExit
