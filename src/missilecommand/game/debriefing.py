import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from itertools import chain

import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.cache import cache
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown

import missilecommand.config as C

from missilecommand.gamestate import gs as GS
from missilecommand.highscoretable import highscoretable
from missilecommand.launchers import mk_textlabel
from missilecommand.types import Comp, EIDs, Prop
from missilecommand.utils import check_for_exit, play_sound


class StatePhase(StrEnum):
    SETUP = auto()
    LINGER_PRE = auto()
    MISSILES = auto()
    CITIES = auto()
    LINGER_POST = auto()


state_machine = StateMachine()
state_machine.add(StatePhase.SETUP, StatePhase.LINGER_PRE)
state_machine.add(StatePhase.LINGER_PRE, StatePhase.MISSILES)
state_machine.add(StatePhase.MISSILES, StatePhase.CITIES)
state_machine.add(StatePhase.CITIES, StatePhase.LINGER_POST)
state_machine.add(StatePhase.LINGER_POST, None)


class Debriefing(GameState):
    def __init__(self, app: App) -> None:
        self.app = app

        self.phase_handlers = {
            StatePhase.SETUP: self.phase_setup_update,
            StatePhase.LINGER_PRE: self.phase_linger_pre_update,
            StatePhase.MISSILES: self.phase_missiles_update,
            StatePhase.CITIES: self.phase_cities_update,
            StatePhase.LINGER_POST: self.phase_linger_post_update,
        }

        self.phase_walker = state_machine.walker()
        self.phase = next(self.phase_walker)

        self.it_missiles = iter(list(chain(*(b for b in GS.batteries))))
        self.missile_pos = C.POS_MISSILES_DEBRIEFING.copy()

        self.it_city_eids = (f'city-{i}' for i, city in enumerate(GS.cities) if city)
        self.city_list_pos = C.POS_CITIES_DEBRIEFING.copy()

        msg = C.MESSAGES['debriefing']['BONUS POINTS']
        mk_textlabel(*msg, EIDs.BONUS_POINTS)
        mk_textlabel('  0', C.POS_MISSILES_SCORE_DEBRIEFING, 'midright', 'red', (1, 1), EIDs.MISSILES_LABEL)
        mk_textlabel('   0', C.POS_CITIES_SCORE_DEBRIEFING, 'midright', 'red', (1, 1), EIDs.CITIES_LABEL)
        ecs.set_property(EIDs.BONUS_POINTS, Prop.IS_DEBRIEFING)
        ecs.set_property(EIDs.MISSILES_LABEL, Prop.IS_DEBRIEFING)
        ecs.set_property(EIDs.CITIES_LABEL, Prop.IS_DEBRIEFING)

        self.cd_linger_pre = Cooldown(2)
        self.cd_linger_post = Cooldown(3)
        self.cd_count = Cooldown(0.1)

        self.missile_score = 0
        self.city_score = 0

    def dispatch_event(self, e):
        check_for_exit(e)

    def update(self, dt):
        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)

    def phase_setup_update(self, dt):
        self.cd_linger_pre.reset()
        self.phase = next(self.phase_walker)

    def phase_linger_pre_update(self, dt):
        if self.cd_linger_pre.cold():
            self.cd_count.reset(0.1)
            self.phase = next(self.phase_walker)

    def phase_missiles_update(self, dt):
        if not self.cd_count.cold(): return

        try:
            eid = next(self.it_missiles)
        except StopIteration:
            self.phase = next(self.phase_walker)
            self.cd_count.reset()
        else:
            prev_score = GS.score // C.BONUS_CITY_SCORE

            self.missile_score += GS.score_mult * C.Score.UNUSED_MISSILE
            GS.score += GS.score_mult * C.Score.UNUSED_MISSILE
            ecs.add_component(EIDs.MISSILES_LABEL, Comp.TEXT, str(self.missile_score))
            ecs.add_component(EIDs.SCORE, Comp.TEXT, f'{GS.score:5d}  ')

            if GS.score > highscoretable.leader.score:
                ecs.add_component(EIDs.HIGHSCORE, Comp.TEXT, f'{GS.score:5d}')

            prsa = ecs.comp_of_eid(eid, Comp.PRSA)
            prsa.pos = self.missile_pos.copy()
            self.missile_pos.x += C.SPRITESHEET['missiles'][0].width
            ecs.add_component(eid, Comp.ANCHOR, 'midleft')
            play_sound(cache['sounds']['silo-count'])
            self.cd_count.reset()

            if GS.score // C.BONUS_CITY_SCORE > prev_score:
                GS.bonus_cities += 1
                play_sound(cache['sounds']['bonus-city'])

    def phase_cities_update(self, dt):
        if not self.cd_count.cold(): return

        score_pre = GS.score // C.BONUS_CITY_SCORE

        try:
            eid = next(self.it_city_eids)
        except StopIteration:
            self.phase = next(self.phase_walker)
            self.cd_linger_post.reset()
        else:
            self.city_score += GS.score_mult * C.Score.CITY
            GS.score += GS.score_mult * C.Score.CITY
            ecs.add_component(EIDs.CITIES_LABEL, Comp.TEXT, str(self.city_score))
            ecs.add_component(EIDs.SCORE, Comp.TEXT, f'{GS.score:5d}  ')
            if GS.score > highscoretable.leader.score:
                ecs.add_component(EIDs.HIGHSCORE, Comp.TEXT, f'{GS.score:5d}')

            prsa = ecs.comp_of_eid(eid, Comp.PRSA)
            prsa.pos = self.city_list_pos.copy()
            self.city_list_pos.x += C.SPRITESHEET['small-cities'][0].width * 1.2
            ecs.add_component(eid, Comp.ANCHOR, 'midleft')
            play_sound(cache['sounds']['silo-count'])
            self.cd_count.reset(0.275)

        new_bonus_cities = GS.score // C.BONUS_CITY_SCORE - score_pre
        if new_bonus_cities > 0:
            GS.bonus_cities += new_bonus_cities
            play_sound(cache['sounds']['bonus-city'])

    def phase_linger_post_update(self, dt):
        if not self.cd_linger_post.cold(): return
        self.teardown()
        raise StateExit

    def draw(self):
        # Since all entities are inside the ECS, the systems of the game state
        # will render them.
        pass

    def teardown(self):
        ecs.purge_by_property(Prop.IS_DEBRIEFING)
