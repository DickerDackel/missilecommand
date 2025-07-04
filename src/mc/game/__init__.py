import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework.app import GameState, StateExit

import mc.globals as G

from mc.game.entities import Silo, City, Target, MissileHead, Trail, Mouse


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
        self.missiles = []
        self.targets = []
        self.trails = []

        self.paused = False

        self.mouse = Mouse(self.app.window_rect, self.app.logical_rect)

    def reset(self):
        self.silos = [Silo(pos) for pos in G.POS_BATTERIES]
        self.cities = [City(pos) for pos in G.POS_CITIES]
        self.missiles.clear()
        self.targets.clear()
        self.trails.clear()

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()

        self.renderer.target = None
        self.renderer.draw_color = G.COLOR.background

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

        self.mouse.update(dt)

        for missile in self.missiles: missile.update(dt)
        for target in self.targets: target.update(dt)
        for trail in self.trails:
            trail.update(dt)

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

    def draw(self):
        ground = cache.get('ground')
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        for city in self.cities: city.draw()
        for silo in self.silos: silo.draw()
        for missile in self.missiles: missile.draw(self.renderer)
        for target in self.targets: target.draw()
        for trail in self.trails: trail.draw()
        self.trail_canvas.draw()

        self.mouse.draw()
        # crosshair = cache.get('crosshair')
        # rect = crosshair.get_rect(center=mouse)
        # crosshair.draw(dstrect=rect)

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
