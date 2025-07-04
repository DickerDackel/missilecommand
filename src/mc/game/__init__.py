import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework.app import GameState, StateExit

import mc.globals as G

from mc.utils import to_viewport
from mc.sprite import TSprite, TAnimSprite


class Silo:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)

        textures = cache.get('missiles')
        self.missiles = [TAnimSprite(self.pos + offset, textures, delay=1)
                         for offset in G.MISSILE_OFFSETS]

    def draw(self):
        for m in self.missiles: m.draw()


class City(TSprite):
    def __init__(self, pos):
        texture = cache.get('city')
        super().__init__(pos, texture, anchor='midbottom')


class Target(TAnimSprite):
    def __init__(self, pos):
        textures = cache.get('targets')
        super().__init__(pos, textures, delay=0.3)

class Missile:
    def __init__(self, pos, destination, speed, renderer, trail_texture):
        self.pos = pos
        self.destination = pygame.Vector2(destination)
        self.speed = speed
        self.renderer = renderer
        self.trail_texture = trail_texture

        self.target = Target(self.destination)

        self.explode = False
        self.trail = []

    def update(self, dt):
        distance = self.destination - self.pos
        speed = self.speed * dt

        if distance.length() < speed:
            step = distance
            self.explode = True
        else:
            step = distance.normalize() * speed

        self.trail.append((self.pos, self.pos + step))
        self.pos = self.trail[-1][1]

        self.target.update(dt)

    def draw(self):
        self.target.draw()

        if not self.trail: return

        save_target = self.renderer.target
        save_color = self.renderer.draw_color

        self.renderer.target = self.trail_texture
        self.renderer.draw_color = G.COLOR.enemy_missile
        self.renderer.draw_line(*self.trail[-1])

        self.renderer.target = save_target
        self.renderer.draw_color = save_color
        self.renderer.draw_point(self.trail[-1][1])

    def kill(self):
        save_target = self.renderer.target
        save_color = self.renderer.draw_color

        self.renderer.target = self.trail_texture
        self.renderer.draw_color = G.COLOR.background
        for t in self.trail:
            self.renderer.draw_line(*t)

        self.renderer.draw_color = save_color
        self.renderer.target = save_target

        self.target = None


class Game(GameState):
    def __init__(self, app):
        self.app = app
        self.renderer = self.app.renderer
        self.scale = self.app.renderer.scale

        pygame.mouse.set_pos(G.SCREEN.center)

        self.trails = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trails.blend_mode = pygame.BLENDMODE_BLEND

        self.silos = []
        self.cities = []
        self.missiles = []

        self.paused = False

    def reset(self):
        self.silos = [Silo(pos) for pos in G.POS_BATTERIES]
        self.cities = [City(pos) for pos in G.POS_CITIES]
        self.missiles.clear()

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trails
        self.renderer.clear()

        self.renderer.target = self.trails
        self.renderer.draw_color = G.COLOR.clear
        self.renderer.clear()

        self.renderer.target = None
        self.renderer.draw_color = G.COLOR.background

    def restart(self, result):
        pass

    def dispatch_event(self, e):
        mouse = to_viewport(pygame.mouse.get_pos(),
                            self.app.window_rect.size,
                            self.app.logical_rect.size)

        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            raise StateExit(-999)
        elif e.type == pygame.KEYDOWN:
            if e.key in G.KEY_SILO_MAP:
                launchpad = G.KEY_SILO_MAP[e.key]
                self.try_missile_launch(launchpad, mouse)
            elif e.key == pygame.K_SPACE:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused: return

        for m in self.missiles:
            m.update(dt)

        explosions = [m for m in self.missiles if m.explode]
        for e in explosions:
            e.kill()
            self.missiles.remove(e)
            self.launch_explosion(e.pos)

    def draw(self):
        ground = cache.get('ground')
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        for city in self.cities: city.draw()
        for silo in self.silos: silo.draw()
        for missile in self.missiles: missile.draw()
        self.trails.draw()

        mp = pygame.mouse.get_pos()
        mouse = to_viewport(mp, self.app.window_rect.size, self.app.logical_rect.size)
        crosshair = cache.get('crosshair')
        rect = crosshair.get_rect(center=mouse)
        crosshair.draw(dstrect=rect)

    def try_missile_launch(self, launchpad, destination):
        if not self.silos[launchpad].missiles: return

        speed = G.MISSILE_SPEEDS[launchpad]
        start = G.POS_LAUNCHPADS[launchpad]
        self.silos[launchpad].missiles.pop()
        self.missiles.append(Missile(start, destination, speed, self.renderer,
                                     self.trails))

    def launch_explosion(self, pos):
        ...
