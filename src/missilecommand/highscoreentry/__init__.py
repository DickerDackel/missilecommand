import logging
logging.info(__name__)  # noqa: E402

from typing import Any

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from pgcooldown import Cooldown
from pygame import Vector2 as vec2

import missilecommand.config as C

from missilecommand.gamestate import gs as GS
from missilecommand.highscoretable import highscoretable
from missilecommand.launchers import mk_textlabel, mk_texture
from missilecommand.systems import sys_draw_texture, sys_draw_textlabel
from missilecommand.types import Comp
from missilecommand.utils import check_for_exit, play_sound

LETTERS = [k for k in C.CHAR_MAP.keys() if len(k) == 1]  # Don't use the sym names like 'copy' here


class HighscoreEntry(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

    def reset(self, *args, **kwargs):
        self.entities = []

        pos = vec2(C.GRID(15, 3, 2, 1).center)
        self.entities.append(mk_textlabel('   ', pos, 'center', C.COLOR.initials, eid='entry'))

        msg = C.MESSAGES['highscore entry']['PLAYER  ']
        self.entities.append(mk_textlabel(*msg))
        self.entities.append(mk_textlabel(*msg))
        ecs.add_component(self.entities[-1], Comp.TEXT, '       1')
        ecs.add_component(self.entities[-1], Comp.COLOR, C.COLOR.special_text)

        msg = C.MESSAGES['highscore entry']['GREAT SCORE']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['highscore entry']['ENTER YOUR INITIALS']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['highscore entry']['SPIN BALL TO CHANGE LETTER']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['highscore entry']['PRESS ANY FIRE SWITCH TO SELECT']
        self.entities.append(mk_textlabel(*msg))

        self.entities.append(mk_texture(cache['textures']['ground'], PRSA(pos=C.GRID.midbottom), 'midbottom'))

        self.letter_idx = 1
        self.entry_no = 0
        self.entry = [LETTERS[self.letter_idx], LETTERS[0], LETTERS[0]]
        self.cd_scroll = Cooldown(C.HIGHSCORE_ENTRY_SCROLL_COOLDOWN)

    def dispatch_event(self, e: pygame.event.Event) -> None:
        check_for_exit(e)

        if e.type == pygame.KEYDOWN:
            if e.key in {pygame.K_q, pygame.K_w, pygame.K_e}:
                play_sound(cache['sounds']['diiuuu'])
                self.entry_no += 1
                if self.entry_no >= len(self.entry):
                    return

            self.entry[self.entry_no] = LETTERS[self.letter_idx]

        elif e.type == pygame.MOUSEWHEEL:
            if self.cd_scroll.cold():
                self.cd_scroll.reset()
                self.letter_idx = (self.letter_idx + e.y) % len(LETTERS)
                play_sound(cache['sounds']['silo-count'])
            self.entry[self.entry_no] = LETTERS[self.letter_idx]

    def update(self, dt: float) -> None:
        if self.entry_no >= len(self.entry):
            self.teardown()
            raise StateExit

        ecs.add_component('entry', Comp.TEXT, ''.join(self.entry))

    def draw(self) -> None:
        self.app.renderer.draw_color = C.COLOR.background
        self.app.renderer.clear()
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self):
        highscoretable.append([GS.score, ''.join(self.entry)])

        for eid in self.entities:
            ecs.remove_entity(eid)
