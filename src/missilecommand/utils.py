import logging
logging.info(__name__)  # noqa: E402

from typing import Hashable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pygame.typing import ColorLike, Point

from pgcooldown import remap

import missilecommand.config as C
from missilecommand.soundpool import soundpool


def check_for_exit(e):
    if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        raise SystemExit(-1)


def cls(texture: sdl2.Texture, color: ColorLike = 'black') -> None:
    """clear the given texture"""
    renderer = texture.renderer
    bkp_target = renderer.target
    bkp_color = renderer.draw_color

    renderer.target = texture
    renderer.draw_color = color
    renderer.clear()

    renderer.target = bkp_target
    renderer.draw_color = bkp_color


def constraint_mouse(window, renderer, rect):
    sclx, scly = renderer.scale
    m_rect = rect.scale_by(sclx, scly).move_to(topleft=(0, 0))
    window.mouse_rect = m_rect


def debug_rect(renderer, rect, color='red'):
    bkp_color = renderer.draw_color
    renderer.draw_color = color
    renderer.draw_rect(rect)
    renderer.draw_color = bkp_color


def play_sound(sound: pygame.mixer.Sound, *args, **kwargs) -> int:
    if not C.PLAY_AUDIO: return None

    return sound.play(*args, **kwargs)


def pause_all_sounds():
    for c in soundpool:
        if c.get_busy():
            c.pause()


def unpause_all_sounds():
    for c in soundpool:
        if c.get_busy():
            c.unpause()


def purge_entities(property: Hashable) -> None:
    for eid in ecs.eids_by_property(property):
        ecs.remove_entity(eid)


def stop_all_sounds():
    for c in soundpool:
        if c.get_busy():
            c.stop()


def to_viewport(pos: Point, real_size: tuple[int, int], virtual_size: tuple[int, int]) -> Point:
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


__all__ = ['cls', 'constraint_mouse', 'debug_rect', 'pause_all_sounds',
           'play_sound', 'purge_entities', 'stop_all_sounds', 'to_viewport',
           'unpause_all_sounds']
