#!/bin/env python3

from os import environ
from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework import App

import mc.globals as G

from mc.states.game import Game

# cache.debug = True

def load_atlas(renderer, fname):
    spritesheet = pygame.image.load(fname)
    t = sdl2.Texture.from_surface(renderer, spritesheet)
    cache.add(t, 'spritesheet')

    cache.create_atlas('spritesheet')
    cache.add_to_atlas('spritesheet', 'crosshair', G.SPRITESHEET_CROSSHAIR)
    cache.add_to_atlas('spritesheet', 'target', G.SPRITESHEET_TARGET)
    cache.add_to_atlas('spritesheet', 'missile', G.SPRITESHEET_MISSILE)
    cache.add_to_atlas('spritesheet', 'big-city', G.SPRITESHEET_BIG_CITY)
    cache.add_to_atlas('spritesheet', 'city', G.SPRITESHEET_CITY)
    cache.add_to_atlas('spritesheet', 'alien-big-green', G.SPRITESHEET_ALIEN_BIG_GREEN)
    cache.add_to_atlas('spritesheet', 'alien-big-red', G.SPRITESHEET_ALIEN_BIG_RED)
    cache.add_to_atlas('spritesheet', 'alien-green', G.SPRITESHEET_ALIEN_GREEN)
    cache.add_to_atlas('spritesheet', 'alien-red', G.SPRITESHEET_ALIEN_RED)
    cache.add_to_atlas('spritesheet', 'plane-green', G.SPRITESHEET_PLANE_GREEN)
    cache.add_to_atlas('spritesheet', 'plane-red', G.SPRITESHEET_PLANE_RED)
    cache.add_to_atlas('spritesheet', 'smartbomb-green', G.SPRITESHEET_SMARTBOMB_GREEN)
    cache.add_to_atlas('spritesheet', 'smartbomb-red', G.SPRITESHEET_SMARTBOMB_RED)

    cache.add_to_atlas('spritesheet', 'ground', G.SPRITESHEET_GROUND)


def main():
    app = App(G.TITLE, resolution=G.SCREEN.size, fps=G.FPS)
    pygame.mouse.set_visible(False)

    load_atlas(app.renderer, G.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(game=Game(app))
    app.state_machine.add(states.game, states.game)
    app.create_state_walker(states.game)

    app.run()

if __name__ == "__main__":
    main()
