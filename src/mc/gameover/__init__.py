import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from typing import Any

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown, LerpThing
from pygame import Vector2 as vec2

import mc.config as C

from mc.launchers import mk_textlabel
from mc.systems import (sys_apply_scale, sys_textcurtain, sys_textlabel,
                        sys_texture, sys_texture_from_texture_list)
from mc.types import Comp

EXPLOSION_EID = 'explosion'
TEXT_EID = 'text'

class GameoverPhase(StrEnum):
    SETUP = auto()
    GROWING = auto()
    TEXT = auto()
    SHRINKING = auto()
    LINGERING = auto()


class Gameover(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app

        self.sm = StateMachine()
        self.sm.add(GameoverPhase.SETUP, GameoverPhase.GROWING)
        self.sm.add(GameoverPhase.GROWING, GameoverPhase.TEXT)
        self.sm.add(GameoverPhase.TEXT, GameoverPhase.SHRINKING)
        self.sm.add(GameoverPhase.SHRINKING, GameoverPhase.LINGERING)
        self.sm.add(GameoverPhase.LINGERING, None)
        self.phase_walker = self.sm.walker()
        self.phase = next(self.phase_walker)

        self.phase_handlers = {
            GameoverPhase.SETUP: self.phase_setup_update,
            GameoverPhase.GROWING: self.phase_growing_update,
            GameoverPhase.TEXT: self.phase_text_update,
            GameoverPhase.SHRINKING: self.phase_shrinking_update,
            GameoverPhase.LINGERING: self.phase_lingering_update,
        }

        self.cd_linger = Cooldown(3)
        self.it_text = iter(('       ',
                             'TH     ',
                             'THE    ',
                             'THE    ',
                             'THE E  ',
                             'THE EN ',
                             'THE END'))
        self.cd_it_text = Cooldown(1)

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        texture = cache['gameover']
        prsa = PRSA(pos=vec2(self.app.logical_rect.center))
        scale = LerpThing(0.1, self.app.logical_rect.height / 128, 1.5, repeat=0)

        eid = ecs.create_entity(EXPLOSION_EID)
        ecs.add_component(eid, Comp.TEXTURE, texture)
        ecs.add_component(eid, Comp.PRSA, prsa)
        ecs.add_component(eid, Comp.SCALE, scale)

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
        update_fn = self.phase_handlers[self.phase]
        print(self.phase)
        update_fn(dt)
        print('return')

    def phase_setup_update(self, dt: float) -> None:
        self.phase = next(self.phase_walker)

    def phase_growing_update(self, dt: float) -> None:
        print('inside growing')
        scale = ecs.comp_of_eid(EXPLOSION_EID, Comp.SCALE)
        if scale.finished():
            mk_textlabel('THE END',
                         self.app.logical_rect.center,
                         'center', 'yellow',
                         scale=(3, 6), eid=TEXT_EID)

            curtain = LerpThing(0, 1, 0.5, repeat=0)

            ecs.add_component(TEXT_EID, Comp.TEXT_CURTAIN, curtain)
            ecs.add_component(TEXT_EID, Comp.ANCHOR, 'midleft')

            self.cd_it_text.reset()

            self.phase = next(self.phase_walker)
            return

        ecs.run_system(dt, sys_apply_scale, Comp.PRSA, Comp.SCALE)

    def phase_text_update(self, dt: float) -> None:
        scale = ecs.comp_of_eid(TEXT_EID, Comp.TEXT_CURTAIN)
        if scale.finished():
            scale = LerpThing(self.app.logical_rect.height / 128, 0.01, 1.5, repeat=0)
            self.phase = next(self.phase_walker)
            return

        # ecs.run_system(dt, sys_apply_scale, Comp.PRSA, Comp.SCALE, )


    def phase_shrinking_update(self, dt: float) -> None:
        scale = ecs.comp_of_eid(EXPLOSION_EID, Comp.SCALE)
        if scale.finished():
            self.cd_linger.reset()

            self.phase = next(self.phase_walker)
            return

    def phase_lingering_update(self, dt: float) -> None:
        if self.cd_linger.cold():
            raise StateExit

    def draw(self) -> None:
        self.app.renderer.draw_color = C.COLOR.gameover
        self.app.renderer.clear()

        ecs.run_system(0, sys_texture, Comp.TEXTURE, Comp.PRSA)
        # ecs.run_system(0, sys_curtain, Comp.TEXTURE, Comp.PRSA, Comp.SCALE)
        ecs.run_system(0, sys_textcurtain, Comp.TEXT, Comp.PRSA, Comp.ANCHOR,
                       Comp.COLOR, Comp.TEXT_CURTAIN)

    def teardown(self) -> None:
        ecs.remove_entity(self.state_label)
        raise StateExit
