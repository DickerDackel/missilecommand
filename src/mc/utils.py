import logging
logging.info(__name__)  # noqa: E402

from pygame.typing import Point

from pgcooldown import remap


def to_viewport(pos: Point, real_size: tuple[int, int], virtual_size: tuple[int, int]) -> Point:
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


__all__ = ['to_viewport']
