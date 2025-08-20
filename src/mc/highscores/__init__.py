import logging
logging.info(__name__)  # noqa: E402

from heapq import nlargest
from typing import Any

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown
from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache

import mc.config as C

from mc.highscoretable import highscoretable
from mc.launchers import mk_textlabel, mk_texture
from mc.systems import sys_draw_texture, sys_textlabel
from mc.types import Comp


class Highscores(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app
        self.entities = []

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        msg = C.MESSAGES['HIGH SCORES']
        self.entities.append(mk_textlabel(*msg, eid='high scores'))

        msg = C.MESSAGES['BONUS CITY EVERY POINTS']
        self.entities.append(mk_textlabel(*msg, eid='bonus city 1'))
        self.entities.append(mk_textlabel(*msg, eid='bonus city 2'))
        ecs.add_component(self.entities[-1], Comp.COLOR, C.COLOR.special_text)
        ecs.add_component(self.entities[-1], Comp.TEXT, '                 10000       ')

        msg = C.MESSAGES['DEFEND']
        self.entities.append(mk_textlabel(*msg, eid='defend'))

        msg = C.MESSAGES['CITIES']
        self.entities.append(mk_textlabel(*msg, eid='cities'))

        for y, (score, initials) in enumerate(nlargest(len(highscoretable), highscoretable)):
            msg = C.MessageConfig(f'{initials} {score:8}',
                                  C.GRID(15, y + 4, 2, 1).center,
                                  'center',
                                  C.COLOR.special_text)
            self.entities.append(mk_textlabel(*msg, eid=f'hst-{y}'))

        self.entities.append(mk_texture(cache['textures']['ground'],
                                        C.GRID.midbottom,
                                        'midbottom',
                                        eid='ground'))

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
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self) -> None:
        for l in self.entities:
            ecs.remove_entity(l)

        raise StateExit
