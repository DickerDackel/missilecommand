from enum import StrEnum
from itertools import chain, cycle
from random import choice, randint, sample

import pygame
import pygame._sdl2 as sdl2

from pgcooldown import Cooldown

import ddframework.cache as cache

from ddframework.app import GameState, StateExit, StackPermissions
from ddframework.statemachine import StateMachine

import mc.globals as G

from mc.game.entities import (Silo, City, Target, MissileHead, Trail, Mouse, Explosion)
from mc.game.briefing import Briefing
from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.types import GamePhase
from mc.game.waves import wave_iter
from mc.sprite import TGroup

state_machine = StateMachine()
state_machine.add(GamePhase.SETUP, GamePhase.BRIEFING)
state_machine.add(GamePhase.BRIEFING, GamePhase.PLAYING)
state_machine.add(GamePhase.PLAYING, GamePhase.END_OF_WAVE)
state_machine.add(GamePhase.END_OF_WAVE, GamePhase.DEBRIEFING)
state_machine.add(GamePhase.DEBRIEFING, GamePhase.SETUP)


class Game(GameState):
    def __init__(self, app):
        self.app = app
        self.renderer = self.app.renderer
        self.scale = self.app.renderer.scale

        pygame.mouse.set_pos(G.SCREEN.center)

        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

        self.silos = []
        self.trails = []
        self.cities = TGroup()
        self.attacks = TGroup()
        self.missiles = TGroup()
        self.targets = TGroup()
        self.explosions = TGroup()

        self.paused = False

        self.mouse = Mouse(self.app.window_rect, self.app.logical_rect)

        self.level = 0
        self.wave = None
        self.wave_iter = None
        self.cd_attacks = Cooldown(2, cold=True)

        self.phase_walker = None

    def reset(self):
        self.level = 0
        self.wave_iter = wave_iter()

        self.phase_walker = state_machine.walker()
        self.phase = next(self.phase_walker)

    def setup_wave(self):
        self.attacks.empty()
        self.missiles.empty()
        self.cities.empty()
        self.trails.clear()
        self.targets.empty()
        self.explosions.empty()

        self.silos = [Silo(pos) for pos in G.POS_BATTERIES]
        self.cities.add(City(pos) for pos in G.POS_CITIES)

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()

        self.renderer.target = None
        self.renderer.draw_color = G.COLOR.background

        self.allowed_targets = cycle(chain(self.silos, sample(self.cities.sprites(), k=3)))

        self.wave = next(self.wave_iter)
        self.score_mult = self.level // 2 + 1
        self.cd_attacks.reset(2)
        self.to_launch = self.wave.missiles

    def restart(self, from_state, result):
        pass

    def dispatch_event(self, e):
        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            raise StateExit()
        elif e.type == pygame.KEYDOWN:
            if e.key in G.KEY_SILO_MAP:
                launchpad = G.KEY_SILO_MAP[e.key]
                self.try_missile_launch(launchpad, self.mouse.pos)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)

    def update(self, dt):
        if self.paused: return
        if self.app.is_stacked(self): return

        if self.phase is GamePhase.SETUP:
            self.setup_wave()
            self.phase = next(self.phase_walker)

        elif self.phase is GamePhase.BRIEFING:
            self.phase = next(self.phase_walker)
            self.app.push(Briefing(self.app, 1),
                          passthrough=StackPermissions.DRAW)

        elif self.phase is GamePhase.PLAYING:
            self.update_playing_phase(dt)
            if self.to_launch == 0 and not self.attacks:
                self.phase = next(self.phase_walker)

        elif self.phase is GamePhase.END_OF_WAVE:
            self.update_playing_phase(dt)

            if not self.missiles and not self.attacks and not self.explosions:
                self.phase = next(self.phase_walker)

        elif self.phase is GamePhase.DEBRIEFING:
            self.phase = next(self.phase_walker)
            self.app.push(Debriefing(self.app, self.silos, self.cities),
                          passthrough=StackPermissions.DRAW)

        elif self.phase is GamePhase.GAMEOVER:
            ...

    def update_playing_phase(self, dt):
        def launch_attack(target, speed_frames, rect, renderer, texture):
            start = (randint(0, rect.width), -5)
            speed = speed_frames
            missile = MissileHead(start, target.pos, speed)
            trail = Trail(start, missile, renderer, texture)

            return missile, trail

        if self.cd_attacks.cold():
            self.cd_attacks.reset()
            count = min(G.MISSILES_PER_WAVE, self.to_launch)
            for i in range(count):
                missile, trail = launch_attack(next(self.allowed_targets),
                                               self.wave.missile_speed,
                                               self.app.logical_rect,
                                               self.renderer,
                                               self.trail_canvas)
                self.attacks.add(missile)
                self.trails.append(trail)

            self.to_launch -= count

        self.mouse.update(dt)

        for o in self.attacks: o.update(dt)
        for o in self.missiles: o.update(dt)
        for o in self.targets: o.update(dt)
        for o in self.trails: o.update(dt)
        for o in self.explosions: o.update(dt)

        dead_trails = [o for o in self.trails if o.parent.explode]
        for o in dead_trails:
            o.kill()
            self.trails.remove(o)

        dead_targets = [o for o in self.targets if o.parent.explode]
        for o in dead_targets:
            o.kill()

        dead_missiles = [o for o in chain(self.missiles, self.attacks) if o.explode]
        for o in dead_missiles:
            self.launch_explosion(o.pos)
            o.kill()

        collisions = pygame.sprite.groupcollide(self.explosions, self.attacks,
                                                False, False,
                                                collided=Explosion.collidepoint)
        for explosion, missiles in collisions.items():
            for m in missiles:
                m.explode = True

    def draw(self):
        ground = cache.get('ground')
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        for o in self.cities: o.draw()
        for o in self.silos: o.draw()

        for o in self.trails: o.draw()
        self.trail_canvas.draw()

        for o in self.attacks: o.draw(self.renderer)
        for o in self.missiles: o.draw(self.renderer)
        for o in self.targets: o.draw()

        for o in self.explosions: o.draw()

        self.app.renderer.draw_color = 'grey'
        self.app.renderer.draw_rect(self.app.logical_rect)

        self.mouse.draw()

    def try_missile_launch(self, launchpad, target):
        if not self.silos[launchpad].missiles: return

        speed = G.MISSILE_SPEEDS[launchpad]
        start = G.POS_LAUNCHPADS[launchpad]
        self.silos[launchpad].missiles.pop()
        missile = MissileHead(start, target, speed)
        self.targets.add(Target(target, missile))
        self.missiles.add(missile)
        self.trails.append(Trail(start, missile, self.app.renderer, self.trail_canvas))

    def launch_explosion(self, pos):
        self.explosions.add(Explosion(pos))
