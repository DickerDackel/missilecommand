#!/bin/env python3

# Must follow after loading of ddframework.app
import logging
logging.basicConfig(level=logging.DEBUG)  # noqa: E402
logging.info(__name__)  # noqa: E402

from pathlib import Path
from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

from ddframework.app import App
from ddframework.cache import cache
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game import Game


pygame.init()


def load_sounds(assets: Path) -> None:
    sounds = ('brzzz.wav', 'diiuuu.wav', 'explosion.wav', 'gameover.wav', 'launch.wav')

    cache['sounds'] = {fname.stem: pygame.mixer.Sound(fname)
                       for fname in (assets / f for f in sounds)}


def load_spritesheet(renderer: sdl2.Renderer, fname: str) -> None:
    def ss2t(i: pygame.Surface, r: pygame.Rect) -> sdl2.Texture:
        return sdl2.Texture.from_surface(renderer, i.subsurface(r))

    spritesheet = pygame.image.load(fname)
    cache['spritesheet'] = sdl2.Texture.from_surface(renderer, spritesheet)

    for k, v in C.SPRITESHEET.items():  # noqa: bad-assignment
        if isinstance(v, (list, tuple)):
            images = [ss2t(spritesheet, img) for img in v]
            cache[k] = images
        else:
            cache[k] = ss2t(spritesheet, v)


def main() -> None:
    w = pygame.Window(size=(1024, 960))
    app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    pygame.mouse.set_visible(False)

    load_sounds(C.ASSETS)
    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(game=Game(app))
    sm = StateMachine()
    sm.add(states.game, states.game)
    walker = sm.walker(states.game)

    app.run(walker)


if __name__ == "__main__":
    main()
