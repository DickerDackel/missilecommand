from itertools import chain, cycle
from random import choice, randint, sample

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache
from pgcooldown import Cooldown

from ddframework.app import GameState, StateExit
from ddframework.statemachine import StateMachine

import mc.globals as G

from mc.game.entities import Silo, City, Target, MissileHead, Trail, Mouse
from mc.game.waves import wave_iter


state_machine = StateMachine()
state_machine.add('prep', 'play')
state_machine.add('play', 'score')
state_machine.add('score', 'prep')


class Game(GameState):
    def __init__(self, app):
        self.app = app
        self.renderer = self.app.renderer
        self.scale = self.app.renderer.scale

        pygame.mouse.set_pos(G.SCREEN.center)

        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

        self.silos = []
        self.cities = []
        self.attacks = []
        self.missiles = []
        self.targets = []
        self.trails = []

        self.paused = False

        self.mouse = Mouse(self.app.window_rect, self.app.logical_rect)

        self.level = 0
        self.wave = None
        self.wave_iter = None
        self.missiles_cooldown = Cooldown(2, cold=True)

    def reset(self):
        self.level = 0
        self.wave_iter = wave_iter()
        self.level_reset()

    def level_reset(self):
        self.silos = [Silo(pos) for pos in G.POS_BATTERIES]
        self.cities = [City(pos) for pos in G.POS_CITIES]
        self.attacks.clear()
        self.missiles.clear()
        self.targets.clear()
        self.trails.clear()

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()

        self.renderer.target = None
        self.renderer.draw_color = G.COLOR.background

        self.next_target = cycle(chain(self.silos, sample(self.cities, k=3)))

        self.wave = next(self.wave_iter)
        self.score_mult = self.level // 2 + 1
        self.missiles_cooldown.reset(2)
        self.to_launch = self.wave.missiles

    def restart(self, result):
        pass

    def dispatch_event(self, e):
        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            raise StateExit(-999)
        elif e.type == pygame.KEYDOWN:
            if e.key in G.KEY_SILO_MAP:
                launchpad = G.KEY_SILO_MAP[e.key]
                self.try_missile_launch(launchpad, self.mouse.pos)
            elif e.key == pygame.K_SPACE:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused: return

        def launch_attack(target, speed_frames, rect, renderer, texture):
            start = (randint(0, rect.width), -5)
            speed = speed_frames
            missile = MissileHead(start, target.pos, speed)
            trail = Trail(start, missile, renderer, texture)

            return missile, trail

        if self.missiles_cooldown.cold():
            self.missiles_cooldown.reset()
            count = min(G.MISSILES_PER_WAVE, self.to_launch)
            for i in range(count):
                missile, trail = launch_attack(next(self.next_target),
                                               self.wave.missile_speed,
                                               self.app.logical_rect,
                                               self.renderer,
                                               self.trail_canvas)
                self.attacks.append(missile)
                self.trails.append(trail)

            self.to_launch -= count

        self.mouse.update(dt)

        for o in self.attacks: o.update(dt)
        for o in self.missiles: o.update(dt)
        for o in self.targets: o.update(dt)
        for o in self.trails: o.update(dt)

        explosions = [m for m in self.missiles if m.explode]
        explosions = [
            (head, target, trail)
            for head, target, trail in zip(self.missiles, self.targets, self.trails)
            if head.explode]
        for head, target, trail in explosions:
            trail.kill()
            self.missiles.remove(head)
            self.targets.remove(target)
            self.trails.remove(trail)
            self.launch_explosion(target.pos)

        explosions = [m for m in self.attacks if m.explode]
        explosions = [
            (head, trail)
            for head, trail in zip(self.attacks, self.trails)
            if head.explode]
        for head, trail in explosions:
            trail.kill()
            self.attacks.remove(head)
            self.trails.remove(trail)
            self.launch_explosion(head.pos)

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

        self.mouse.draw()

    def try_missile_launch(self, launchpad, target):
        if not self.silos[launchpad].missiles: return

        speed = G.MISSILE_SPEEDS[launchpad]
        start = G.POS_LAUNCHPADS[launchpad]
        self.silos[launchpad].missiles.pop()
        missile = MissileHead(start, target, speed)
        self.missiles.append(missile)
        self.trails.append(Trail(start, missile, self.app.renderer, self.trail_canvas))
        self.targets.append(Target(target))

    def launch_explosion(self, pos):
        ...
