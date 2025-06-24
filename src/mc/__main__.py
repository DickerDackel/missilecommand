#!/bin/env python3

from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework import App

import mc.globals as G

from mc.states.game import Game

# cache.debug = True

def load_spritesheet(renderer, fname):
    spritesheet = pygame.image.load(fname)
    t = sdl2.Texture.from_surface(renderer, spritesheet)
    cache.add(t, 'spritesheet')

    cache.create_atlas('spritesheet')
    cache.add_to_atlas('spritesheet', 'missile', G.SPRITESHEET_MISSILE)
    cache.add_to_atlas('spritesheet', 'big-city', G.SPRITESHEET_BIG_CITY)
    cache.add_to_atlas('spritesheet', 'city', G.SPRITESHEET_CITY)
    cache.add_to_atlas('spritesheet', 'crosshair', G.SPRITESHEET_CROSSHAIR)
    cache.add_to_atlas('spritesheet', 'ground', G.SPRITESHEET_GROUND)


def main():
    app = App(G.TITLE, G.SCREEN, G.FPS, bgcolor=G.COLOR.background)
    app.renderer.logical_size = G.SCREEN.size
    pygame.mouse.set_relative_mode(True)
    app.renderer.set_viewport(app.renderer.get_viewport().move_to(topleft=(0,0)))
    print(app.renderer.get_viewport())

    load_spritesheet(app.renderer, G.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(game=Game(app))
    app.state_machine.add(states.game, states.game)
    app.create_state_walker(states.game)

    app.run()

if __name__ == "__main__":
    main()
