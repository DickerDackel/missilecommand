from itertools import chain, cycle
from random import choice, randint, sample

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache
from pgcooldown import Cooldown

from ddframework.app import GameState, StateExit
from ddframework.statemachine import StateMachine

import mc.globals as G

from mc.game.entities import Silo, City, Target, MissileHead, Trail, Mouse, Explosion
from mc.game.waves import wave_iter
from mc.sprite import TGroup


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
        self.trails = []
        self.cities = TGroup()
        self.missiles = TGroup()
        self.targets = TGroup()
        self.explosions = TGroup()

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
        self.trails.clear()

        self.cities.empty()
        self.missiles.empty()
        self.targets.empty()
        self.explosions.empty()

        self.cities.add(City(pos) for pos in G.POS_CITIES)

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()

        self.renderer.target = None
        self.renderer.draw_color = G.COLOR.background

        self.next_target = cycle(chain(self.silos, sample(self.cities.sprites(), k=3)))

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
                self.missiles.add(missile)
                self.trails.append(trail)

            self.to_launch -= count

        self.mouse.update(dt)

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

        dead_missiles = [o for o in self.missiles if o.explode]
        for o in dead_missiles:
            self.launch_explosion(o.pos)
            o.kill()

        collisions = pygame.sprite.groupcollide(self.explosions, self.missiles,
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

        for o in self.missiles: o.draw(self.renderer)
        for o in self.targets: o.draw()

        for o in self.explosions: o.draw()

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
