import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Sequence
from typing import Callable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from pgcooldown import LerpThing
from pygame import Vector2 as vec2

from pygame.typing import ColorLike, Point

# from ddframework.msgbroker import broker

import mc.config as C

from mc.game.launchers import mk_explosion, mk_trail_eraser
from mc.game.types import Comp, EIDs
from mc.types import EntityID, Momentum, Trail


def sys_apply_scale(dt: float,
                    eid: EntityID,
                    prsa: PRSA,
                    scale: Callable) -> None:
    PRSA.scale = scale()


def sys_container(dt: float,
                  eid: EntityID,
                  prsa: PRSA,
                  container: pygame.Rect) -> None:
    if not container.collidepoint(prsa.pos):
        ecs.set_property(eid, Comp.IS_DEAD)


def sys_explosion(dt: float,
                  eid: EntityID,
                  textures: Callable,
                  prsa: PRSA,
                  scale: LerpThing) -> None:
    if scale.finished():
        ecs.remove_entity(eid)
        return

    prsa.scale = scale()


def sys_momentum(dt: float, eid: EntityID, prsa: PRSA, momentum: Momentum) -> None:
    if eid == EIDs.FLYER:
        print(f'{eid=} : {prsa.pos=}  {momentum=}')
    prsa.pos += momentum * dt


def sys_mouse(dt: float, eid: EntityID, prsa: PRSA, *, remap: Callable) -> None:
    mp = remap(pygame.mouse.get_pos())
    prsa.pos = vec2(mp)


def sys_move_towards(dt: float,
                     eid: EntityID,
                     prsa: PRSA,
                     target: EntityID,
                     speed: float,
                     trail: list[tuple[Point, Point]]) -> None:
    logging.debug('sys_move_towards')
    logging.debug(f'    {eid=}')
    logging.debug(f'    {prsa=}')
    logging.debug(f'    {target=}')
    logging.debug(f'    {speed=}')
    logging.debug(f'    {trail=}')
    tprsa = ecs.comp_of_eid(target, Comp.PRSA)

    step = prsa.pos.move_towards(tprsa.pos, speed * dt)
    trail.append((prsa.pos, step))
    prsa.pos = step
    if prsa.pos == tprsa.pos:
        ecs.remove_entity(eid)
        ecs.remove_entity(target)
        mk_explosion(tprsa.pos)
        mk_trail_eraser(trail)


def sys_shutdown(dt: float, eid: float, callback: Callable) -> None:
    if isinstance(callback, Sequence):
        for cb in callback:
            cb()
    else:
        callback()


def sys_textlabel(dt: float, eid: EntityID, text: str,
                  prsa: PRSA, anchor: str, color: ColorLike) -> None:
    font = cache['letters']
    crect = font[0].get_rect().scale_by(prsa.scale)
    rect = crect.scale_by(len(text), 1)
    setattr(rect, anchor, prsa.pos)
    crect.midleft = rect.midleft

    for c in text:
        letter = font[C.CHAR_MAP[c]]
        bkp_color = letter.color
        letter.color = color
        letter.draw(dstrect=crect)
        letter.color = bkp_color
        crect.midleft = crect.midright


def sys_texture(dt: float, eid: EntityID, texture: sdl2.Texture,
                prsa: PRSA) -> None:
    # tpos = round(prsa.pos.x), round(prsa.pos.y)
    # rect = texture.get_rect().scale_by(prsa.scale).move_to(center=tpos)
    if eid == EIDs.FLYER: print(eid)
    rect = texture.get_rect().scale_by(prsa.scale).move_to(center=prsa.pos)
    bkp_alpha = texture.alpha

    texture.alpha = prsa.alpha  # ty: ignore
    texture.draw(dstrect=rect, angle=prsa.rotation)

    texture.alpha = bkp_alpha


def sys_textures(dt: float, eid: EntityID, textures: Callable,
                 prsa: PRSA) -> None:
    t = textures()
    ecs.add_component(eid, Comp.TEXTURE, t)


def sys_trail(dt: float,
              eid: EntityID,
              trail: list[tuple[Point, Point]],
              *, texture: sdl2.Texture) -> None:
    renderer = texture.renderer
    bkp_target = renderer.target
    bkp_color = renderer.draw_color

    renderer.target = texture
    renderer.draw_color = C.COLOR.defense_missile

    start, goal = trail[-1]
    renderer.draw_line(start, goal)

    renderer.draw_color = bkp_color
    renderer.target = bkp_target


def sys_trail_eraser(dt: float,
                     eid: EntityID,
                     trail: Trail,
                     *, texture: sdl2.Texture) -> None:
    renderer = texture.renderer
    bkp_target = renderer.target
    bkp_color = renderer.draw_color

    renderer.target = texture
    renderer.draw_color = C.COLOR.clear

    for start, goal in trail:
        renderer.draw_line(start, goal)

    renderer.draw_color = bkp_color
    renderer.target = bkp_target
    ecs.remove_entity(eid)


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
