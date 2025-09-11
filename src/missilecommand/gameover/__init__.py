import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from typing import Any

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.autosequence import AutoSequence
from ddframework.cache import cache
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown, LerpThing
from pygame.math import Vector2 as vec2
from rpeasings import in_quad

import missilecommand.config as C

from missilecommand.launchers import mk_gameover_explosion, mk_gameover_text
from missilecommand.systems import (sys_apply_scale, sys_colorcycle, sys_colorize,
                        sys_textcurtain, sys_draw_textlabel, sys_draw_texture)
from missilecommand.types import Comp, Prop
from missilecommand.utils import check_for_exit, play_sound, purge_entities

EXPLOSION_EID = 'explosion'
TEXT_EID = 'text'


class GameoverPhase(StrEnum):
    SETUP = auto()
    GROWING = auto()
    TEXT = auto()
    SHRINKING = auto()
    LINGERING = auto()


class Gameover(GameState):
    # Yes, this could be generated.  Would be less readable and not worth the
    # effort.  Not even after also writing this comment.
    texts = ('       ',
             'T      ',
             'TH     ',
             'THE    ',
             'THE    ',
             'THE E  ',
             'THE EN ',
             'THE END')

    def __init__(self, app: 'App') -> None:
        self.app: App = app

        self.sm = StateMachine()
        self.sm.add(GameoverPhase.SETUP, GameoverPhase.GROWING)
        self.sm.add(GameoverPhase.GROWING, GameoverPhase.TEXT)
        self.sm.add(GameoverPhase.TEXT, GameoverPhase.SHRINKING)
        self.sm.add(GameoverPhase.SHRINKING, GameoverPhase.LINGERING)
        self.sm.add(GameoverPhase.LINGERING, None)
        self.phase_walker = None
        self.phase = None

        self.phase_handlers = {
            GameoverPhase.SETUP: self.phase_setup_update,
            GameoverPhase.GROWING: self.phase_growing_update,
            GameoverPhase.TEXT: self.phase_text_update,
            GameoverPhase.SHRINKING: self.phase_shrinking_update,
            GameoverPhase.LINGERING: self.phase_lingering_update,
        }

        self.cd_linger = Cooldown(1.5)
        self.the_end = AutoSequence(self.texts, 2, repeat=0, loops=1)

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        self.phase_walker = self.sm.walker()
        self.phase = next(self.phase_walker)

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        elif e.type == pygame.KEYDOWN:
            elif e.key == pygame.K_SPACE:
                self.teardown()
                raise StateExit
            elif e.key == pygame.K_1:
        check_for_exit(e)
        if e.type == pygame.KEYDOWN:
                raise StateExit(1)

    def update(self, dt: float) -> None:
        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)

        ecs.run_system(dt, sys_colorcycle, Comp.COLOR_CYCLE)
        ecs.run_system(dt, sys_colorize, Comp.TEXTURE, Comp.COLOR)

    def phase_setup_update(self, dt: float) -> None:
        play_sound(cache['sounds']['gameover'])
        mk_gameover_explosion(pos=vec2(self.app.logical_rect.center),
                              scale=self.app.logical_rect.height / 128,
                              eid=EXPLOSION_EID)

        self.phase = next(self.phase_walker)

    def phase_growing_update(self, dt: float) -> None:
        scale = ecs.comp_of_eid(EXPLOSION_EID, Comp.SCALE)
        if scale.finished():
            self.phase = next(self.phase_walker)

            self.the_end.reset(0.5)
            mk_gameover_text(self.the_end, self.the_end(),
                             self.app.logical_rect.center, 'center',
                             C.COLOR.gameover, scale=(3, 19), eid=TEXT_EID)

            return

        ecs.run_system(dt, sys_apply_scale, Comp.PRSA, Comp.SCALE)

    def phase_text_update(self, dt: float) -> None:
        if self.the_end.lt.finished():
            scale = LerpThing(self.app.logical_rect.height / 128, 0.1, 1.5, repeat=0, ease=in_quad)
            ecs.add_component(EXPLOSION_EID, Comp.SCALE, scale)
            self.phase = next(self.phase_walker)
            return

        ecs.run_system(dt, sys_textcurtain, Comp.TEXT_SEQUENCE)

    def phase_shrinking_update(self, dt: float) -> None:
        scale = ecs.comp_of_eid(EXPLOSION_EID, Comp.SCALE)
        if scale.finished():
            ecs.remove_entity(EXPLOSION_EID)
            self.cd_linger.reset()
            self.phase = next(self.phase_walker)

            return

        ecs.run_system(dt, sys_apply_scale, Comp.PRSA, Comp.SCALE)

    def phase_lingering_update(self, dt: float) -> None:
        if self.cd_linger.cold():
            raise StateExit

    def draw(self) -> None:
        self.app.renderer.draw_color = C.COLOR.gameover
        self.app.renderer.clear()

        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def teardown(self) -> None:
        purge_entities(Prop.IS_GAMEOVER)
        raise StateExit
