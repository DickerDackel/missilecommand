from itertools import chain

import pygame

from ddframework.app import GameState
from ddframework.app import StateExit
from ddframework.statemachine import StateMachine
from pgcooldown import Cooldown

import mc.globals as G

from mc.game.entities import TString
from mc.game.types import DebriefingPhase


state_machine = StateMachine()
state_machine.add(DebriefingPhase.SETUP, DebriefingPhase.LINGER_PRE)
state_machine.add(DebriefingPhase.LINGER_PRE, DebriefingPhase.MISSILES)
state_machine.add(DebriefingPhase.MISSILES, DebriefingPhase.CITIES)
state_machine.add(DebriefingPhase.CITIES, DebriefingPhase.LINGER_POST)
state_machine.add(DebriefingPhase.LINGER_POST, DebriefingPhase.LINGER_PRE)


class Debriefing(GameState):
    def __init__(self, app, parent, silos, cities):
        self.app = app
        self.parent = parent

        self.phase_walker = state_machine.walker()
        self.phase = next(self.phase_walker)

        self.missiles = list(chain(*(s.missiles for s in silos)))
        self.it_missiles = iter(self.missiles)
        self.missile_pos = G.POS_MISSILES_DEBRIEFING.copy()

        self.cities = cities
        self.it_cities = (city for city in cities if not city.ruined)
        self.cities_pos = G.POS_CITIES_DEBRIEFING.copy()

        label = 'BONUS POINTS'
        self.bonus_points = TString(G.MESSAGES[label][0],
                                    label,
                                    color=G.MESSAGES[label][2],
                                    anchor='midleft')
        self.missiles_label = TString(G.POS_MISSILES_DEBRIEFING - (30, 0),
                                      '0', anchor='midright', color='red')
        self.cities_label = TString(G.POS_CITIES_DEBRIEFING - (30, 0), '0',
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
            self.cd_linger_pre.reset()
            self.phase = next(self.phase_walker)

        elif self.phase is DebriefingPhase.LINGER_PRE:
            if self.cd_linger_pre.cold:
                self.cd_missiles.reset()
                self.phase = next(self.phase_walker)

        elif self.phase is DebriefingPhase.MISSILES:
            if not self.cd_missiles.cold(): return

            try:
                missile = next(self.it_missiles)
            except StopIteration:
                self.phase = next(self.phase_walker)
                self.cd_cities.reset()
            else:
                self.parent.score += G.Score.UNUSED_MISSILE
                self.missile_score += G.Score.UNUSED_MISSILE
                self.missiles_label = TString(G.POS_MISSILES_DEBRIEFING - (30, 0),
                                              str(self.missile_score),
                                              anchor='midright', color='red')
                missile.anchor = 'midleft'
                missile.pos = self.missile_pos
                missile.update(dt)
                self.missile_pos.x += missile.rect.width
                self.cd_missiles.reset()

        elif self.phase is DebriefingPhase.CITIES:
            if not self.cd_cities.cold(): return

            try:
                city = next(self.it_cities)
            except StopIteration:
                self.phase = next(self.phase_walker)
                self.cd_linger_post.reset()
            else:
                self.parent.score += G.Score.CITY
                self.city_score += G.Score.CITY
                self.cities_label = TString(G.POS_CITIES_DEBRIEFING - (30, 0),
                                            str(self.city_score),
                                            anchor='midright', color='red')
                city.anchor = 'midleft'
                city.pos = self.cities_pos
                city.update(dt)
                self.cities_pos.x += city.rect.width
                self.cd_cities.reset()

        elif self.phase is DebriefingPhase.LINGER_POST:
            if not self.cd_linger_post.cold(): return

            raise StateExit(None)

    def draw(self):
        self.bonus_points.draw()
        self.missiles_label.draw()
        self.cities_label.draw()

        for o in self.missiles: o.draw()
        for o in self.cities: o.draw()
