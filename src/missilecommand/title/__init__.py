from enum import StrEnum, auto
from random import randint, triangular
from typing import Any

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown, LerpThing
from pygame import _sdl2 as sdl2
from pygame import Vector2 as vec2

import missilecommand.config as C
from missilecommand.launchers import mk_explosion, mk_quickhelp
from missilecommand.systems import (non_ecs_sys_prune, sys_draw_textlabel,
                                    sys_draw_texture, sys_explosion,
                                    sys_shutdown, sys_textblink,
                                    sys_texture_from_texture_list)
from missilecommand.types import Comp, Prop
from missilecommand.utils import check_for_exit, draw_text, play_sound


def sys_create_crater(dt, eid, prsa, texture=None):
    if prsa.scale < 0.98: return

    ecs.remove_property(eid, Prop.IS_GROWING)

    renderer = texture.renderer
    bkp_target = renderer.target

    renderer.target = texture
    crater = cache['textures']['crater']
    crater.draw(dstrect=crater.get_rect().move_to(center=prsa.pos))

    renderer.target = bkp_target


class TitlePhase(StrEnum):
    SETUP = auto()
    PRE_BOMB = auto()
    BOMB = auto()
    POST_BOMB = auto()
    LINGERING = auto()


phases = StateMachine()
phases.add(TitlePhase.SETUP, TitlePhase.PRE_BOMB)
phases.add(TitlePhase.PRE_BOMB, TitlePhase.BOMB)
phases.add(TitlePhase.BOMB, TitlePhase.POST_BOMB)
phases.add(TitlePhase.POST_BOMB, TitlePhase.LINGERING)
phases.add(TitlePhase.LINGERING, None)


class Title(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app
        self.renderer = self.app.renderer
        self.phase_walker = None
        self.phase = None

        self.phase_handlers = {
            TitlePhase.SETUP: self.update_phase_setup,
            TitlePhase.PRE_BOMB: self.update_phase_pre_bomb,
            TitlePhase.BOMB: self.update_phase_bomb,
            TitlePhase.POST_BOMB: self.update_phase_post_bomb,
            TitlePhase.LINGERING: self.update_phase_lingering,
        }

        self.cd_pre_bomb = Cooldown(2)
        self.cd_lingering = Cooldown(3)
        self.cd_bomb = Cooldown(0.05)

        self.crater_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.crater_canvas.blend_mode = pygame.BLENDMODE_BLEND

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        txt_missile = C.MESSAGES['title']['MISSILE']
        txt_command = C.MESSAGES['title']['COMMAND']

        bkp_target = self.renderer.target
        bkp_color = self.renderer.draw_color

        self.renderer.target = self.crater_canvas
        self.renderer.draw_color = C.COLOR.clear
        self.renderer.clear()

        draw_text(txt_missile.text, PRSA(pos=txt_missile.pos, scale=txt_missile.scale), anchor=txt_missile.anchor, color=txt_missile.color)
        draw_text(txt_command.text, PRSA(pos=txt_command.pos, scale=txt_command.scale), anchor=txt_command.anchor, color=txt_command.color)

        self.renderer.target = bkp_target
        self.renderer.draw_color = bkp_color

        mk_quickhelp()

        self.phase_walker = phases.walker()
        self.phase = next(self.phase_walker)

        self.explosions = set()

    def restart(self, from_state: 'GameState', result: Any) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        check_for_exit(e)

        self.mouse = self.app.coordinates_from_window(pygame.mouse.get_pos())

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                raise StateExit(1)

    def update(self, dt: float) -> None:
        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)

        ecs.run_system(dt, sys_explosion, Comp.TEXTURE_LIST, Comp.PRSA, Comp.SCALE, has_properties={Prop.IS_EXPLOSION})
        ecs.run_system(dt, sys_shutdown, Comp.SHUTDOWN, has_properties={Prop.IS_DEAD})
        ecs.run_system(dt, sys_create_crater, Comp.PRSA, texture=self.crater_canvas, has_properties={Prop.IS_GROWING})
        ecs.run_system(dt, sys_texture_from_texture_list, Comp.TEXTURE_LIST)

        non_ecs_sys_prune()

    def update_phase_setup(self, dt: float) -> None:
        self.cd_pre_bomb.reset()
        self.phase = next(self.phase_walker)

    def update_phase_pre_bomb(self, dt: float) -> None:
        if self.cd_pre_bomb.cold():
            self.cd_bomb.temperature = 0  # Start already cold
            self.phase = next(self.phase_walker)

            margin = C.EXPLOSION_RADIUS
            self.bomb_x = LerpThing(margin, self.app.logical_rect.width - margin, 0.5)

    def update_phase_bomb(self, dt: float) -> None:
        if self.bomb_x.finished():
            self.phase = next(self.phase_walker)

        if self.cd_bomb.cold():
            self.cd_bomb.reset()
            for i in range(2):
                midline = self.app.logical_rect.height / 3
                y_spread = self.app.logical_rect.height / 4

                pos = vec2(self.bomb_x() + randint(-10, 10),
                           midline + triangular(low=-1, high=1, mode=0) * y_spread)

                def shutdown(eid):
                    self.explosions.remove(eid)

                eid = mk_explosion(pos)
                ecs.set_property(eid, Prop.IS_GROWING)
                ecs.add_component(eid, Comp.SHUTDOWN, shutdown)
                self.explosions.add(eid)
            play_sound(cache['sounds']['explosion'])

    def update_phase_post_bomb(self, dt: float) -> None:
        if self.explosions:
            return

        self.phase = next(self.phase_walker)
        self.cd_lingering.reset()

    def update_phase_lingering(self, dt: float) -> None:
        if self.cd_lingering.cold():
            self.teardown()
            raise StateExit

    def draw(self) -> None:
        # self.app.renderer.draw_color = C.COLOR.background
        # self.app.renderer.clear()

        self.crater_canvas.draw(dstrect=self.app.logical_rect)
        ecs.run_system(0, sys_textblink, Comp.COLOR_CYCLE)
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self) -> None:
        ecs.reset()
