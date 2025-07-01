import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework.app import GameState, StateExit
from pgcooldown import remap

import mc.globals as G


def to_viewport(pos, real_size, virtual_size):
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


class TSprite:
    def __init__(self, pos, atlas, sprite_rect, anchor='center'):
        self.pos = pos
        self.atlas = atlas
        self.srcrect = sprite_rect.copy()
        self.dstrect = sprite_rect.move_to(**{anchor: self.pos})

    def update(self, dt):
        self.dstrect.center = self.pos

    def draw(self):
        self.atlas.draw(srcrect=self.srcrect, dstrect=self.dstrect)

class Silo:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)

        atlas = cache.get('spritesheet')
        missile = cache.get_from_atlas('spritesheet', 'missile')

        self.missiles = [TSprite(self.pos + offset, atlas, missile)
                         for offset in G.MISSILE_OFFSETS]

    def draw(self):
        for m in self.missiles:
            m.draw()


class City:
    def __init__(self, pos):
        self.pos = pos
        atlas = cache.get('spritesheet')
        city = cache.get_from_atlas('spritesheet', 'city')

        self.city = TSprite(self.pos, atlas, city, anchor='midbottom')

    def draw(self):
        self.city.draw()


class Missile:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination


class Game(GameState):
    def __init__(self, app):
        self.app = app
        self.renderer = self.app.renderer
        self.scale = self.app.renderer.scale

        pygame.mouse.set_pos(G.SCREEN.center)

        self.trails = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trails.blend_mode = pygame.BLENDMODE_BLEND

        self.silos = None
        self.targets =None
        self.aam = None

    def reset(self):
        self.silos = [Silo(pos) for pos in G.POS_BATTERIES]
        self.cities = [City(pos) for pos in G.POS_CITIES]

        self.targets = []
        self.aam = []

        self.renderer.draw_color = G.COLOR.clear
        self.renderer.target = self.trails
        self.renderer.clear()

        r = self.app.logical_rect
        self.renderer.draw_color = G.COLOR.grid
        self.renderer.draw_line(r.midtop, r.midbottom)
        self.renderer.draw_line(r.midleft, r.midright)
        print(self.trails.blend_mode)

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
                if self.silos[launchpad].missiles:
                    self.launch_missile(launchpad, mouse)


    def update(self, dt):
        pass

    def draw(self):
        renderer = self.app.renderer

        atlas = cache.get('spritesheet')

        ground = cache.get_from_atlas('spritesheet', 'ground')
        rect = ground.move_to(midbottom=self.app.logical_rect.midbottom)
        atlas.draw(srcrect=ground, dstrect=rect)

        for city in self.cities: city.draw()
        for silo in self.silos: silo.draw()
        for target in self.targets: target.draw()
        self.trails.draw()

        mp = pygame.mouse.get_pos()
        mouse = to_viewport(mp, self.app.window_rect.size, self.app.logical_rect.size)
        crosshair = cache.get_from_atlas('spritesheet', 'crosshair')
        atlas.draw(srcrect=crosshair, dstrect=crosshair.move_to(center=mouse))

    def launch_missile(self, launchpad, destination):
        start = G.POS_LAUNCHPADS[launchpad]
        self.silos[launchpad].missiles.pop()
        self.aam.append(Missile(start, destination))

        atlas = cache.get('spritesheet')
        target = cache.get_from_atlas('spritesheet', 'target')
        self.targets.append(TSprite(destination, atlas, target))
