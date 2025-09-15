#!/bin/env python3

# Must follow after loading of ddframework.app
import logging
logging.info(__name__)  # noqa: E402

import random
import sys

from argparse import ArgumentParser
from os import environ
from pathlib import Path
from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

from ddframework.app import App
from ddframework.cache import cache
from ddframework.statemachine import StateMachine

import missilecommand.config as C

from missilecommand.splash import Splash
from missilecommand.title import Title
from missilecommand.demo import Demo
from missilecommand.highscores import Highscores
from missilecommand.highscoreentry import HighscoreEntry
from missilecommand.game import Game
from missilecommand.gameover import Gameover

if 'XDG_SESSION_TYPE' in environ and environ['XDG_SESSION_TYPE'] == 'wayland':
    environ['SDL_VIDEODRIVER'] = 'wayland'

pygame.init()


def load_sounds(assets: Path) -> None:
    sounds = assets.glob('*.wav')
    cache['sounds'] = {fname.stem: pygame.mixer.Sound(fname)
                       for fname in (assets / f for f in sounds)}
    for s in cache['sounds'].values():
        s.set_volume(0.1)


def load_spritesheet(renderer: sdl2.Renderer, fname: str) -> None:
    def ss2t(i: pygame.Surface, r: pygame.Rect) -> sdl2.Texture:
        return sdl2.Texture.from_surface(renderer, i.subsurface(r))

    def ss2m(i: pygame.Surface, r: pygame.Rect) -> pygame.mask.Mask:
        return pygame.mask.from_surface(i.subsurface(r))

    spritesheet = pygame.image.load(fname)
    cache['textures']['spritesheet'] = sdl2.Texture.from_surface(renderer, spritesheet)

    for k, v in C.SPRITESHEET.items():  # noqa: bad-assignment
        if isinstance(v, (list, tuple)):
            images = [ss2t(spritesheet, rect) for rect in v]
            masks = [ss2m(spritesheet, rect) for rect in v]
            cache['textures'][k] = images
            cache['masks'][k] = masks
        else:
            cache['textures'][k] = ss2t(spritesheet, v)
            cache['masks'][k] = ss2m(spritesheet, v)


def main() -> None:
    cmdline = ArgumentParser(description=C.TITLE)
    cmdline.add_argument('-v', '--verbose', action='count', default=0, help='Enable verbose logging')
    cmdline.add_argument('-q', '--quiet', action='count', default=0, help='Supress even error or crictical log messages')
    cmdline.add_argument('-S', '--stats', action='store_true', default=0, help='Show statistics on exit')
    cmdline.add_argument('-P', '--perftrace', action='store_true', default=0, help='Show live performance data')
    cmdline.add_argument('-U', '--unlimited', action='store_true', default=False, help='Unlimited ammo FIXME')
    opts = cmdline.parse_args(sys.argv[1:])
    opts.verbose = max(min(opts.verbose, 3), 0)
    opts.quiet = max(min(opts.quiet, 2), 0)

    log_level = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ][2 - opts.verbose + opts.quiet]
    logging.basicConfig(level=log_level)  # noqa: E402

    w = pygame.Window(size=(1280, 960), position=pygame.WINDOWPOS_CENTERED)
    app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    # app = App(C.TITLE, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    # pygame.mouse.set_visible(False)

    load_sounds(C.ASSETS)
    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(
        splash=Splash(app),
        title=Title(app),
        demo=Game(app, demo=True),
        highscores=Highscores(app),
        highscoreentry=HighscoreEntry(app),
        game=Game(app),
        gameover=Gameover(app),
    )

    sm = StateMachine()
    sm.add(states.splash, states.title)
    sm.add(states.title, states.demo, states.game)
    sm.add(states.demo, states.highscores, states.game)
    sm.add(states.highscores, states.title, states.game)
    sm.add(states.game, states.gameover, states.highscoreentry)
    sm.add(states.gameover, states.highscores)
    sm.add(states.highscoreentry, states.highscores)
    walker = sm.walker(states.splash)

    app.opts = opts  # FIXME
    app.run(walker, perftrace=opts.perftrace, stats=opts.stats)


if __name__ == "__main__":
    main()
