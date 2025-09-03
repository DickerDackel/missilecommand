import logging
logging.info(__name__)  # noqa: E402

from typing import Hashable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pygame.typing import ColorLike, Point

from pgcooldown import remap

import mc.config as C


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


def play_sound(sound: pygame.mixer.Sound,
               max_instances: int = 0, *args, **kwargs) -> None:
    if not C.PLAY_AUDIO: return

    if max_instances and sound.get_num_channels() > max_instances:
        return

    sound.play(*args, **kwargs)

    return sound


def purge_entities(property: Hashable) -> None:
    for eid in ecs.eids_by_property(property):
        ecs.remove_entity(eid)


def stop_sound(sound: pygame.mixer.Sound | None):
    if sound is not None:
        sound.stop()


def to_viewport(pos: Point, real_size: tuple[int, int], virtual_size: tuple[int, int]) -> Point:
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


__all__ = ['cls', 'debug_rect', 'play_sound', 'purge_entities', 'to_viewport']
