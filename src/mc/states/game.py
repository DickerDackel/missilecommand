import pygame

import ddframework.cache as cache

from ddframework.app import GameState, StateExit

import mc.globals as G


def draw_missile_battery(texture, rect, pos):
    x, y = pos
    y += G.POS_BATTERY_Y_STEP
    x -= 1.5 * G.POS_BATTERY_X_STEP

    for i in range(4):
        texture.draw(srcrect=rect, dstrect=rect.move_to(center=(x, y)))
        x += G.POS_BATTERY_X_STEP
    x -= 3 * G.POS_BATTERY_X_STEP + G.POS_BATTERY_X_STEP / 2
    y -= G.POS_BATTERY_Y_STEP
    for i in range(3):
        texture.draw(srcrect=rect, dstrect=rect.move_to(center=(x, y)))
        x += G.POS_BATTERY_X_STEP
    x -= 2 * G.POS_BATTERY_X_STEP + G.POS_BATTERY_X_STEP / 2
    y -= G.POS_BATTERY_Y_STEP
    for i in range(2):
        texture.draw(srcrect=rect, dstrect=rect.move_to(center=(x, y)))
        x += G.POS_BATTERY_X_STEP
    x -= 1 * G.POS_BATTERY_X_STEP + G.POS_BATTERY_X_STEP / 2
    y -= G.POS_BATTERY_Y_STEP
    texture.draw(srcrect=rect, dstrect=rect.move_to(center=(x, y)))

class Game(GameState):
    def __init__(self, app):
        self.app = app

    def reset(self):
        pass

    def restart(self, result):
        pass

    def dispatch_event(self, e):
        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            raise StateExit(-999)

    def update(self, dt):
        pass

    def draw(self):
        renderer = self.app.renderer

        rect = self.app.rect
        renderer.draw_color = G.COLOR.grid
        renderer.draw_color = 'white'
        for x in range(0, rect.width, 16):
            renderer.draw_line((x, 0), (x, rect.height))
        for y in range(0, rect.height, 16):
            renderer.draw_line((0, y), (rect.width, y))

        atlas = cache.get('spritesheet')

        ground = cache.get_from_atlas('spritesheet', 'ground')
        rect = ground.move_to(midbottom=self.app.rect.midbottom)
        atlas.draw(srcrect=ground, dstrect=rect)

        city =cache.get_from_atlas('spritesheet', 'city')
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_1))
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_2))
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_3))
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_4))
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_5))
        atlas.draw(srcrect=city, dstrect=city.move_to(midbottom=G.POS_CITY_6))

        missile = cache.get_from_atlas('spritesheet', 'missile')
        draw_missile_battery(atlas, missile, G.POS_BATTERY_LEFT)
        draw_missile_battery(atlas, missile, G.POS_BATTERY_CENTER)
        draw_missile_battery(atlas, missile, G.POS_BATTERY_RIGHT)

        mouse = pygame.mouse.get_pos()
        print(mouse)
        crosshair = cache.get_from_atlas('spritesheet', 'crosshair')
        atlas.draw(srcrect=crosshair, dstrect=crosshair.move_to(center=mouse))
