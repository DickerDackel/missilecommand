#!/bin/env python3

from os import environ
from pathlib import Path
from types import SimpleNamespace

import pygame
import pygame._sdl2 as sdl2

from ddframework.app import App
from ddframework.cache import cache
from ddframework.statemachine import StateMachine

import missilecommand.config as C

from missilecommand.debug_layer import DebugLayer
from missilecommand.splash import Splash
from missilecommand.title import Title
from missilecommand.highscores import Highscores
from missilecommand.highscoreentry import HighscoreEntry
from missilecommand.instructions import Instructions
from missilecommand.game import Game
from missilecommand.gameover import Gameover

BANNER = 'Missile Command v0.0.5'


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
    print(BANNER)

    if 'XDG_SESSION_TYPE' in environ and environ['XDG_SESSION_TYPE'] == 'wayland':
        environ['SDL_VIDEODRIVER'] = 'wayland'

    pygame.init()

    # w = pygame.Window(size=C.WINDOW.size, position=pygame.WINDOWPOS_CENTERED)
    # app = App(C.TITLE, window=w, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    app = App(C.TITLE, resolution=C.SCREEN.size, fps=C.FPS, bgcolor=C.COLOR.background)
    pygame.mouse.set_visible(False)

    load_sounds(C.ASSETS)
    load_spritesheet(app.renderer, C.ASSETS.joinpath('spritesheet.png'))

    states = SimpleNamespace(
        splash=Splash(app),
        title=Title(app),
        demo=Game(app, demo=True),
        highscores=Highscores(app),
        instructions=Instructions(app),
        highscoreentry=HighscoreEntry(app),
        game=Game(app),
        gameover=Gameover(app),
    )

    sm = StateMachine()
    sm.add(states.splash, states.instructions)
    sm.add(states.instructions, states.title, states.game)
    sm.add(states.title, states.demo, states.game)
    sm.add(states.demo, states.highscores, states.game)
    sm.add(states.highscores, states.instructions, states.game)
    sm.add(states.game, states.gameover, states.highscoreentry)
    sm.add(states.gameover, states.highscores)
    sm.add(states.highscoreentry, states.highscores)
    walker = sm.walker(states.splash)

    # walker = DebugLayer(app, walker)
    app.run(walker)


if __name__ == "__main__":
    main()
