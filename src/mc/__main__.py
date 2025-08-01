#!/bin/env python3

from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

from ddframework.app import App
from ddframework.cache import cache as CACHE
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game import Game


def load_spritesheet(renderer: sdl2.Renderer, fname: str):
    def ss2t(i: pygame.Surface, r: pygame.Rect) -> sdl2.Texture:
        return sdl2.Texture.from_surface(renderer, i.subsurface(r))

    spritesheet = pygame.image.load(fname)
    CACHE['spritesheet'] = sdl2.Texture.from_surface(renderer, spritesheet)

    for k, v in C.SPRITESHEET.items():  # noqa: bad-assignment
        if isinstance(v, (list, tuple)):
            images = [ss2t(spritesheet, img) for img in v]
            CACHE[k] = images
        else:
            CACHE[k] = ss2t(spritesheet, v)


def main():
    w = pygame.Window(size=(1024, 960))
    app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.Color.background)
    pygame.mouse.set_visible(False)

    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(game=Game(app))
    sm = StateMachine()
    sm.add(states.game, states.game)
    walker = sm.walker(states.game)

    app.run(walker)

if __name__ == "__main__":
    main()
