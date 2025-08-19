import logging
logging.info(__name__)  # noqa: E402

import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from pgcooldown import Cooldown
from pygame import Vector2 as vec2

import mc.config as C

from mc.launchers import mk_textlabel
from mc.types import Comp
from mc.systems import sys_draw_texture, sys_textlabel

LETTERS = [k for k in C.CHAR_MAP.keys() if len(k) == 1]  # Don't use the sym names like 'copy' here

class HighscoreEntry(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

        self.labels = []

        ground = cache['textures']['ground']
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        pos = vec2(C.GRID(7, 3, 2, 1).center)
        self.labels.append(mk_textlabel('   ', pos, 'center', C.COLOR.initials, eid='entry'))

        pos = vec2(C.GRID(7, 5, 2, 1).center)
        self.labels.append(mk_textlabel('PLAYER  ', pos, 'center', C.COLOR.normal_text))
        self.labels.append(mk_textlabel('       1', pos, 'center', C.COLOR.special_text))

        pos = vec2(C.GRID(7, 6, 2, 1).center)
        self.labels.append(mk_textlabel('GREAT SCORE', pos, 'center', C.COLOR.normal_text, scale=(2.5, 1.5)))

        pos = vec2(C.GRID(7, 7, 2, 1).center)
        self.labels.append(mk_textlabel('ENTER YOUR INITIALS', pos, 'center', C.COLOR.normal_text))

        pos = vec2(C.GRID(7, 8, 2, 1).center)
        self.labels.append(mk_textlabel('SPIN BALL TO CHANGE LATTER', pos, 'center', C.COLOR.normal_text))

        pos = vec2(C.GRID(7, 9, 2, 1).center)
        self.labels.append(mk_textlabel('PRESS ANY FIRE SWITCH TO SELECT', pos, 'center', C.COLOR.normal_text))

        self.entry = [LETTERS[0]] * 3
        self.letter_idx = 0
        self.entry_no = 0
        self.cd_scroll = Cooldown(C.HIGHSCORE_ENTRY_SCROLL_COOLDOWN)

    def dispatch_event(self, e: pygame.event.Event) -> None:
        if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
                or e.type == pygame.QUIT):
            self.teardown()

        if e.type == pygame.KEYDOWN and e.key in {pygame.K_q, pygame.K_w, pygame.K_e}:
            self.entry_no += 1
            print(self.entry_no)
            if self.entry_no >= len(self.entry):
                return

            self.entry[self.entry_no] = LETTERS[self.letter_idx]

        elif e.type == pygame.MOUSEWHEEL:
            if self.cd_scroll.cold():
                self.cd_scroll.reset()
                self.letter_idx = (self.letter_idx + e.y) % len(LETTERS)
            self.entry[self.entry_no] = LETTERS[self.letter_idx]
            print(self.letter_idx)

    def update(self, dt: float) -> None:
        if self.entry_no >= len(self.entry):
            print(f'HIGHSCORE: {"".join(self.entry)}')
            self.teardown()

        ecs.add_component('entry', Comp.TEXT, ''.join(self.entry))

    def draw(self) -> None:
        ground = cache['textures']['ground']
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        r = ground.renderer
        bkp = r.draw_color
        r.draw_color = 'red'
        r.draw_rect(C.GRID(7, 3, 2, 1))
        r.draw_rect(C.GRID(7, 5, 2, 1))
        r.draw_rect(C.GRID(7, 6, 2, 1))
        r.draw_rect(C.GRID(7, 7, 2, 1))
        r.draw_rect(C.GRID(7, 8, 2, 1))
        r.draw_rect(C.GRID(7, 9, 2, 1))
        r.draw_color = bkp

        ecs.run_system(0, sys_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self):
        for eid in self.labels:
            ecs.remove_entity(eid)
        raise StateExit(-1)
