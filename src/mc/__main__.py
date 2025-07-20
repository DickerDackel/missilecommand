#!/bin/env python3

from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

import ddframework.cache as cache

from ddframework import App

import mc.config as C

from mc.game import Game


def load_spritesheet(renderer, fname):
    def ss2t(i, r):
        return sdl2.Texture.from_surface(renderer, i.subsurface(r))

    spritesheet = pygame.image.load(fname)
    cache.add(sdl2.Texture.from_surface(renderer, spritesheet), 'spritesheet')

    for k, v in C.SPRITESHEET.items():
        if isinstance(v, (list, tuple)):
            images = [ss2t(spritesheet, img) for img in v]
            cache.add(images, k)
        else:
            cache.add(ss2t(spritesheet, v), k)


def main():
    w = pygame.Window(size=(1024, 960))
    app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    pygame.mouse.set_visible(False)

    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(game=Game(app))
    app.state_machine.add(states.game, states.game)
    app.create_state_walker(states.game)

    app.run()

if __name__ == "__main__":
    main()
