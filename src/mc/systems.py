import pygame

from mc.utils import to_viewport

def sys_mouse_to_pos(dt, eid, pos, wants_mouse, *, real_size, virtual_size):
    mouse = pygame.mouse.get_pos()
    pos.x, pos.y = to_viewport(mouse, real_size, virtual_size)
    print(f'{pos=}  {mouse=}  {real_size=}  {virtual_size=}')

def sys_pos_to_rect(dt, eid, pos, rect):
    anchor = rect.anchor if hasattr(rect, 'anchor') else 'center'
    setattr(rect, anchor, pos)

def sys_draw_texture(dt, eid, texture, rect):
    texture.draw(dstrect=rect)

def sys_mouse(dt, eid, pos, rect, texture, wants_mouse, *, real_size, virtual_size):
    sys_mouse_to_pos(dt, eid, pos, wants_mouse, real_size=real_size, virtual_size=virtual_size)
    sys_pos_to_rect(dt, eid, pos, rect)
    print(f'sys_mouse {pos=}  {rect=}')
    sys_draw_texture(dt, eid, texture, rect)

__all__ = [
    sys_mouse_to_pos,
    sys_pos_to_rect,
    sys_draw_texture,
    sys_mouse,
]
