import logging
logging.info(__name__)  # noqa: E402

import pygame
import tinyecs as ecs

from pgcooldown import Cooldown

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache

import mc.config as C

from mc.launchers import mk_textlabel
from mc.utils import play_sound


class Briefing(GameState):
    def __init__(self, app: App, mult: float) -> None:
        self.app = app

        self.state_label = mk_textlabel('BRIEFING',
                                        self.app.logical_rect.topright,
                                        'topright', 'white', eid='briefingstate_label')

        self.labels = []

        for t in ['PLAYER', 'DEFEND CITIES', 'x POINTS']:
            msg = C.MESSAGES[t]
            eid = mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid=msg.text)
            self.labels.append(eid)

        msg = C.MESSAGES['PLAYER_NO']
        mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid='PLAYER_NO')
        self.labels.append('PLAYER_NO')

        msg = C.MESSAGES['MULT']
        mk_textlabel(msg.text, msg.pos, msg.anchor, msg.color, eid='MULT')
        self.labels.append('MULT')

        self.cd_state = Cooldown(3)
        self.cd_sound = Cooldown(0.4)
        self.sounds_pending = 3

    def teardown(self) -> None:
        ecs.remove_entity(self.state_label)

        for t in self.labels:
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
