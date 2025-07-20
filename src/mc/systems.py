from typing import Callable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pygame import Vector2 as vec2
from pygame.typing import Point

import mc.config as C

from mc.components import Comp, PRSA
from mc.game.entities import mk_trail_eraser
from mc.typing import EntityID, Trail

# Called from draw
def mouse_system(dt: float, eid: EntityID, prsa: PRSA,
                 wants_mouse: bool, *, remap: Callable) -> None:
    mp = remap(pygame.mouse.get_pos())
    prsa.pos = vec2(mp)

def texture_system(dt: float, eid: EntityID, texture: sdl2.Texture,
                   prsa: PRSA, *args) -> None:
    rect = texture.get_rect(center=prsa.pos)
    bkp_alpha = texture.alpha

    texture.alpha = prsa.alpha
    texture.draw(dstrect=rect, angle=prsa.rotation)

    texture.alpha = bkp_alpha

def textures_system(dt: float, eid: EntityID, textures: Callable,
                    prsa: PRSA, *args) -> None:
    t = textures()
    texture_system(dt, eid, t, prsa, *args)

def move_towards_system(dt: float, eid: EntityID, is_missile: bool,
                        prsa: PRSA, target: EntityID, speed: float,
                        trail: list[tuple[Point, Point]], *args) -> None:
    tprsa = ecs.comp_of_eid(target, Comp.PRSA)

    step = prsa.pos.move_towards(tprsa.pos, speed * dt)
    trail.append((prsa.pos, step))
    prsa.pos = step
    if prsa.pos == tprsa.pos:
        ecs.remove_entity(eid)
        ecs.remove_entity(target)
        mk_trail_eraser(trail)

        # mk_explosion(tprsa.pos)

def trail_system(dt: float, eid: EntityID, trail: list[tuple[Point, Point]],
                 *, texture: sdl2.Texture) -> None:
    renderer = texture.renderer
    bkp_target = renderer.target
    bkp_color = renderer.draw_color

    renderer.target = texture
    # renderer.draw_color = C.COLOR.defense_missile
    renderer.draw_color = 'red'

    start, goal = trail[-1]
    renderer.draw_line(start, goal)

    renderer.draw_color = bkp_color
    renderer.target = bkp_target

def trail_eraser_system(dt: float, eid: EntityID, is_dead_trail: bool,
                        trail: Trail, *, texture: sdl2.Texture) -> None:
    renderer = texture.renderer
    bkp_target = renderer.target
    bkp_color = renderer.draw_color

    renderer.target = texture
    renderer.draw_color = C.COLOR.clear

    for start, goal in trail:
        renderer.draw_line(start, goal)

    renderer.draw_color = bkp_color
    renderer.target = bkp_target



# def sys_draw_city(dt, eid, textures, is_ruined, rect):
#     sys_draw_texture(dt, eid, textures[is_ruined], rect)

# def sys_draw_texture(dt, eid, texture, rect):
#     texture.draw(dstrect=rect)

# def momentum_system(dt, eid, rsap, momentum):
#     rsap.pos += momentum * dt

# def sys_pos_to_rect(dt, eid, rsap, rect):
#     anchor = rect.anchor if hasattr(rect, 'anchor') else 'center'
#     setattr(rect, anchor, rsap.pos)

# def sys_missilehead(dt, eid, rsap, target, speed):
#     distance = target - rsap.pos
#     step = speed * dt
#     if distance.length() <= step:
#         dest = distance
#         ecs.add_component(eid, Comp.EXPLODE, True)
#     else:
#         dest = distance.normalize() * step

#     rsap.pos += step

# def sys_trail(dt, eid, start, parent, trail, *, renderer, canvas):
#     ppos = ecs.comp_of_eid(parent, Comp.RSAP)


# __all__ = ['momentum_system', 'sys_draw_city', 'sys_draw_texture',
#            'sys_lerpthing_list', 'sys_missilehead', 'sys_mouse',
#            'sys_pos_to_rect', 'sys_trail']
