import logging
logging.info(__name__)  # noqa: E402

from heapq import nlargest
from itertools import chain
from typing import Any

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown
from ddframework.app import App, GameState, StateExit
from ddframework.autosequence import AutoSequence
from ddframework.cache import cache

import mc.config as C

from mc.highscoretable import highscoretable
from mc.launchers import mk_battery, mk_city, mk_textlabel, mk_texture
from mc.systems import (sys_draw_texture, sys_draw_textlabel, sys_textblink,
                        sys_texture_from_texture_list)
from mc.types import Comp

THIS = 'highscores'


class Highscores(GameState):
    def __init__(self, app: 'App') -> None:
        self.app: App = app
        self.entities = []

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()

        def tag_entity(eid):
            ecs.set_property(eid, THIS)
            return eid

        for msg in C.MESSAGES[THIS].values():
            tag_entity(mk_textlabel(*msg))

        for t in {'DEFEND', 'CITIES', '↓ DEFEND', '↓ CITIES'}:
            tag_entity(mk_textlabel(*C.MESSAGES['briefing'][t]))

        for t in {'↓ DEFEND', '↓ CITIES'}:
            msg = C.MESSAGES['briefing'][t]
            eid = tag_entity(mk_textlabel(*C.MESSAGES['briefing'][t]))
            ecs.add_component(eid, Comp.COLOR_CYCLE, AutoSequence((msg.color, C.COLOR.background)))

        for y, (score, initials) in enumerate(nlargest(len(highscoretable), highscoretable)):
            msg = C.MessageConfig(f'{initials} {score:8}',
                                  C.GRID(15, y + 4, 2, 1).center, 'center', C.COLOR.special_text)
            tag_entity(mk_textlabel(*msg))

        eid = tag_entity(mk_texture(cache['textures']['ground'], C.GRID.midbottom, 'midbottom'))
        ecs.set_property(eid, THIS)

        for pos in C.POS_CITIES:
            tag_entity(mk_city(pos))

        for i, pos in enumerate(C.POS_BATTERIES):
            battery, silos = mk_battery(i, pos)
            ecs.set_property(battery, THIS)
            for silo in silos:
                ecs.set_property(silo, THIS)

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
        ecs.run_system(0, sys_textblink, Comp.COLOR_CYCLE)
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)
        ecs.run_system(0, sys_texture_from_texture_list, Comp.TEXTURE_LIST)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

    def teardown(self) -> None:
        ecs.purge_by_property(THIS)
        print(ecs.eidx)
        raise StateExit
