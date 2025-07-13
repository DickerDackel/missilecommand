import pygame
import pygame._sdl2 as sdl2

from pgcooldown import remap

def to_viewport(pos, real_size, virtual_size):
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))


def colorize(texture, color):
    renderer = texture.renderer
    rect = texture.get_rect()

    bkp_target = renderer.target
    bkp_draw_color = renderer.draw_color

    result = sdl2.Texture(texture.renderer, rect.size, target=True)
    result.blend_mode = pygame.BLENDMODE_BLEND
    renderer.target = result
    renderer.draw_color = (0x40, 0x40, 0x40, 0)
    renderer.clear()

    color_texture = sdl2.Texture(renderer, rect.size, target=True)
    color_texture.blend_mode = pygame.BLEND_RGBA_MULT
    renderer.target = color_texture
    renderer.draw_color = color
    renderer.clear()

    renderer.target = result
    texture.draw(dstrect=rect)
    color_texture.draw(dstrect=rect)

    renderer.draw_color = bkp_draw_color
    renderer.target = bkp_target

    return result
__all__ = ['to_viewport']
