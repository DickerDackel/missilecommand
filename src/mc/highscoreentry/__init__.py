import logging
logging.info(__name__)  # noqa: E402

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from pgcooldown import Cooldown
from pygame import Vector2 as vec2

import mc.config as C

from mc.highscoretable import highscoretable
from mc.launchers import mk_textlabel, mk_texture
from mc.systems import sys_draw_texture, sys_textlabel
from mc.types import Comp
from mc.utils import play_sound

LETTERS = [k for k in C.CHAR_MAP.keys() if len(k) == 1]  # Don't use the sym names like 'copy' here

class HighscoreEntry(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

    def reset(self, *args, **kwargs):
        self.entities = []

        pos = vec2(C.GRID(15, 3, 2, 1).center)
        self.entities.append(mk_textlabel('   ', pos, 'center', C.COLOR.initials, eid='entry'))

        msg = C.MESSAGES['HIGHSCORE ENTRY']['PLAYER  ']
        self.entities.append(mk_textlabel(*msg))
        self.entities.append(mk_textlabel(*msg))
        ecs.add_component(self.entities[-1], Comp.TEXT, '       1')
        ecs.add_component(self.entities[-1], Comp.COLOR, C.COLOR.special_text)

        msg = C.MESSAGES['HIGHSCORE ENTRY']['GREAT SCORE']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['HIGHSCORE ENTRY']['ENTER YOUR INITIALS']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['HIGHSCORE ENTRY']['SPIN BALL TO CHANGE LETTER']
        self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['HIGHSCORE ENTRY']['PRESS ANY FIRE SWITCH TO SELECT']
        self.entities.append(mk_textlabel(*msg))

        self.entities.append(mk_texture(cache['textures']['ground'], C.GRID.midbottom, 'midbottom'))

        self.entry = [LETTERS[0]] * 3
        self.letter_idx = 0
        self.entry_no = 0
        self.cd_scroll = Cooldown(C.HIGHSCORE_ENTRY_SCROLL_COOLDOWN)

    def dispatch_event(self, e: pygame.event.Event) -> None:
        if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
                or e.type == pygame.QUIT):
            self.teardown()

        if e.type == pygame.KEYDOWN and e.key in {pygame.K_q, pygame.K_w, pygame.K_e}:
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

        ecs.add_component('entry', Comp.TEXT, ''.join(self.entry))

    def draw(self) -> None:
        ecs.run_system(0, sys_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self):
        for eid in self.entities:
            ecs.remove_entity(eid)
        raise StateExit
