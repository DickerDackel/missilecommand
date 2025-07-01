from itertools import cycle

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework.app import GameState, StateExit
from pgcooldown import Cooldown, remap

import mc.globals as G


def to_viewport(pos, real_size, virtual_size):
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


class TSprite:
    def __init__(self, pos, atlas, sprite_rect, anchor='center'):
        self.pos = pos
        self.atlas = atlas
        self.anchor = anchor

        self.srcrect = sprite_rect.copy()
        self.dstrect = sprite_rect.move_to(**{anchor: self.pos})

    def update(self, dt):
        print(f'{self.anchor=}  {self.pos=}')
        setattr(self.dstrect, self.anchor, self.pos)

    def draw(self):
        self.atlas.draw(srcrect=self.srcrect, dstrect=self.dstrect)


class TSpriteAnim(TSprite):
    def __init__(self, pos, atlas, sprite_rects, anchor='center', delay=1/60):
        super().__init__(pos, atlas, sprite_rects[0], anchor)
        self.textures = cycle(sprite_rects)
        self.cooldown = Cooldown(delay)

    def update(self, dt):
        if self.cooldown.cold():
            self.srcrect = next(self.textures)
            self.cooldown.reset()

        super().update(dt)

    def draw(self):
        super().draw()



class Silo:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)

        atlas = cache.get('spritesheet')
        texture = cache.get_from_atlas('spritesheet', 'missile')
        self.missiles = [TSprite(self.pos + offset, atlas, texture)
                         for offset in G.MISSILE_OFFSETS]

    def draw(self):
        for m in self.missiles: m.draw()


class City(TSprite):
    def __init__(self, pos):
        atlas = cache.get('spritesheet')
        texture = cache.get_from_atlas('spritesheet', 'city')
        super().__init__(pos, atlas, texture, anchor='midbottom')


class Missile:
    def __init__(self, pos, destination, speed, renderer, trail_texture):
        self.pos = pos
        self.destination = pygame.Vector2(destination)
        self.speed = speed
        self.renderer = renderer
        self.trail_texture = trail_texture

        atlas = cache.get('spritesheet')
        textures = cache.get_from_atlas('spritesheet', 'targets')
        self.crosshair = TSpriteAnim(self.destination, atlas, textures, delay=0.1)

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

        self.crosshair.update(dt)

    def draw(self):
        self.crosshair.draw()

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

        self.crosshair = None


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
        renderer = self.app.renderer

        atlas = cache.get('spritesheet')

        ground = cache.get_from_atlas('spritesheet', 'ground')
        rect = ground.move_to(midbottom=self.app.logical_rect.midbottom)
        atlas.draw(srcrect=ground, dstrect=rect)

        for city in self.cities: city.draw()
        for silo in self.silos: silo.draw()
        for missile in self.missiles: missile.draw()
        self.trails.draw()

        mp = pygame.mouse.get_pos()
        mouse = to_viewport(mp, self.app.window_rect.size, self.app.logical_rect.size)
        crosshair = cache.get_from_atlas('spritesheet', 'crosshair')
        atlas.draw(srcrect=crosshair, dstrect=crosshair.move_to(center=mouse))

    def try_missile_launch(self, launchpad, destination):
        if not self.silos[launchpad].missiles: return

        speed = G.MISSILE_SPEEDS[launchpad]
        start = G.POS_LAUNCHPADS[launchpad]
        self.silos[launchpad].missiles.pop()
        self.missiles.append(Missile(start, destination, speed, self.renderer,
                                     self.trails))

    def launch_explosion(self, pos):
        ...
