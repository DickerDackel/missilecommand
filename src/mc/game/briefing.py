import logging
logging.info(__name__)  # noqa: E402

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown

from ddframework.app import App, GameState, StateExit
from ddframework.autosequence import AutoSequence
from ddframework.cache import cache

import mc.config as C

from mc.launchers import mk_textlabel
from mc.types import Comp
from mc.utils import play_sound


class Briefing(GameState):
    def __init__(self, app: App, mult: float, cities: int) -> None:
        self.app = app

        self.entities = []

        for t in {'PLAYER', 'DEFEND', 'CITIES', 'x POINTS', 'PLAYER_NO'}:
            msg = C.MESSAGES['briefing'][t]
            self.entities.append(mk_textlabel(*msg))

        msg = C.MESSAGES['briefing']['MULT']
        self.entities.append(mk_textlabel(f'{mult}{msg.text[1:]}', *msg[1:]))

        for t in {'↓ DEFEND', '↓ CITIES'}:
            msg = C.MESSAGES['briefing'][t]
            self.entities.append(mk_textlabel(*msg))
            ecs.add_component(self.entities[-1], Comp.COLOR_CYCLE, AutoSequence((C.COLOR.special_text, C.COLOR.background)))

        self.cd_state = Cooldown(3)
        self.cd_sound = Cooldown(0.35)
        self.sounds_pending = cities

    def teardown(self) -> None:
        for t in self.entities:
            ecs.remove_entity(t)

    def dispatch_events(self, e: pygame.event.Event) -> None:
        if e.key == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.teardown()
            raise StateExit(-1)

    def update(self, dt: float) -> None:
        if self.cd_state.cold():
            self.teardown()
            raise StateExit(-1)

        if self.cd_sound.cold() and self.sounds_pending:
            play_sound(cache['sounds']['diiuuu'])
            self.sounds_pending -= 1
            self.cd_sound.reset()

    def draw(self) -> None:
        ...  # FIXME
