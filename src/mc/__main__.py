#!/bin/env python3

# Must follow after loading of ddframework.app
import logging
logging.basicConfig(level=logging.INFO)  # noqa: E402
logging.info(__name__)  # noqa: E402

import sys

from argparse import ArgumentParser
from pathlib import Path
from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

from ddframework.app import App
from ddframework.cache import cache
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.splash import Splash
from mc.title import Title
from mc.demo import Demo
from mc.highscores import Highscores
from mc.game import Game
from mc.gameover import Gameover


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
    cmdline = ArgumentParser(description=C.TITLE)
    cmdline.add_argument('-v', '--verbose', action='count', default=0, help='Enable verbose logging')
    cmdline.add_argument('-s', '--stats', action='store_true', default=0, help='Show statistics on exit')
    opts = cmdline.parse_args(sys.argv[1:])

    log_level = [
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ][max(min(5, opts.verbose), 0)]
    logging.basicConfig(level=log_level)  # noqa: E402

    w = pygame.Window(size=(1024, 960))
    app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    pygame.mouse.set_visible(False)

    load_sounds(C.ASSETS)
    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(
        splash=Splash(app),
        title=Title(app),
        demo=Demo(app),
        highscores=Highscores(app),
        game=Game(app),
        gameover=Gameover(app),
    )

    sm = StateMachine()
    sm.add(states.splash, states.title)
    sm.add(states.title, states.demo, states.game)
    sm.add(states.demo, states.highscores, states.game)
    sm.add(states.highscores, states.title, states.game)
    sm.add(states.game, states.gameover)
    sm.add(states.gameover, states.highscores)
    walker = sm.walker(states.splash)

    app.run(walker, verbose=opts.verbose, stats=opts.stats)


if __name__ == "__main__":
    main()
