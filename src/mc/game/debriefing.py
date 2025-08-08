import logging
logging.info(__name__)  # noqa: E402

from itertools import chain

import pygame

from ddframework.app import App, GameState
from ddframework.app import StateExit
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown

import mc.config as C

from mc.game.types import DebriefingPhase


state_machine = StateMachine()
state_machine.add(DebriefingPhase.SETUP, DebriefingPhase.LINGER_PRE)
state_machine.add(DebriefingPhase.LINGER_PRE, DebriefingPhase.MISSILES)
state_machine.add(DebriefingPhase.MISSILES, DebriefingPhase.CITIES)
state_machine.add(DebriefingPhase.CITIES, DebriefingPhase.LINGER_POST)
state_machine.add(DebriefingPhase.LINGER_POST, DebriefingPhase.LINGER_PRE)


class Debriefing(GameState):
    def __init__(self, app: App, parent, silos, cities) -> None:
        self.app = app
        self.parent = parent

        # FIXME
        self.state_label = mk_textlabel('DEBRIEFING',
                                        self.app.logical_rect.topright,
                                        'topright', 'white', eid='debriefingstate_label')

        self.phase_walker = state_machine.walker()
        self.phase = next(self.phase_walker)

        self.missiles = list(chain(*(s.missiles for s in silos)))
        self.it_missiles = iter(self.missiles)
        self.missile_pos = C.POS_MISSILES_DEBRIEFING.copy()

        self.cities = cities
        self.it_cities = (city for city in cities if not city.ruined)
        self.cities_pos = C.POS_CITIES_DEBRIEFING.copy()

        label = 'BONUS POINTS'
        self.bonus_points = TString(C.MESSAGES[label][0],
                                    label,
                                    color=C.MESSAGES[label][2],
                                    anchor='midleft')
        self.missiles_label = TString(C.POS_MISSILES_DEBRIEFING - (30, 0),
                                      '0', anchor='midright', color='red')
        self.cities_label = TString(C.POS_CITIES_DEBRIEFING - (30, 0), '0',
                                    anchor='midright', color='red')

        self.cd_linger_pre = Cooldown(2)
        self.cd_missiles = Cooldown(0.075)
        self.cd_cities = Cooldown(0.3)
        self.cd_linger_post = Cooldown(3)

        self.paused = False

        self.score = 0
        self.missile_score = 0
        self.city_score = 0

    def dispatch_events(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
            self.paused = not self.paused

    def update(self, dt):
        if self.paused: return

        if self.phase is DebriefingPhase.SETUP:
            self.update_setup_phase(dt)
        elif self.phase is DebriefingPhase.LINGER_PRE:
            self.update_linger_pre_phase(dt)
        elif self.phase is DebriefingPhase.MISSILES:
            self.update_missiles_phase(dt)
        elif self.phase is DebriefingPhase.CITIES:
            self.update_cities_phase(dt)
        elif self.phase is DebriefingPhase.LINGER_POST:
            self.update_linger_post_phase(dt)
        else:
            raise RuntimeError('state machinen is b0rken')

    def draw(self):
        self.bonus_points.draw()
        self.missiles_label.draw()
        self.cities_label.draw()

        for o in self.missiles: o.draw()
        for o in self.cities: o.draw()

    def update_setup_phase(self, dt):
        self.cd_linger_pre.reset()
        self.phase = next(self.phase_walker)

    def update_linger_pre_phase(self, dt):
        if self.cd_linger_pre.cold:
            self.cd_missiles.reset()
            self.phase = next(self.phase_walker)

    def update_missiles_phase(self, dt):
        if not self.cd_missiles.cold(): return

        try:
            missile = next(self.it_missiles)
        except StopIteration:
            self.phase = next(self.phase_walker)
            self.cd_cities.reset()
        else:
            self.parent.score += C.Score.UNUSED_MISSILE
            self.missile_score += C.Score.UNUSED_MISSILE
            self.missiles_label = TString(C.POS_MISSILES_DEBRIEFING - (30, 0),
                                          str(self.missile_score),
                                          anchor='midright', color='red')
            missile.anchor = 'midleft'
            missile.pos = self.missile_pos
            missile.update(dt)
            self.missile_pos.x += missile.rect.width
            self.cd_missiles.reset()

    def update_cities_phase(self, dt):
        if not self.cd_cities.cold(): return

        try:
            city = next(self.it_cities)
        except StopIteration:
            self.phase = next(self.phase_walker)
            self.cd_linger_post.reset()
        else:
            self.parent.score += C.Score.CITY
            self.city_score += C.Score.CITY
            self.cities_label = TString(C.POS_CITIES_DEBRIEFING - (30, 0),
                                        str(self.city_score),
                                        anchor='midright', color='red')
            city.anchor = 'midleft'
            city.pos = self.cities_pos
            city.update(dt)
            self.cities_pos.x += city.rect.width
            self.cd_cities.reset()

    def update_linger_post_phase(self, dt):
        if not self.cd_linger_post.cold(): return

        ecs.remove_entity(self.state_label)
        raise StateExit(-1)
