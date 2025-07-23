import pygame

from pgcooldown import remap

from mc.config import GRID

def to_viewport(pos, real_size, virtual_size):
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))

def debug_grid(renderer):
        bkp_color = renderer.draw_color
        renderer.draw_color = 'darkslategrey'

        renderer.draw_rect(GRID(0, 0, 16, 16))

        for x in range(16):
            for y in range(16):
                rect = GRID(x, y)
                renderer.draw_rect(pygame.Rect(*rect))

        renderer.draw_color = bkp_color

__all__ = ['to_viewport']

