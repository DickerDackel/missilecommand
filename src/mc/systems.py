import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Sequence
from typing import Callable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from pgcooldown import Cooldown, LerpThing
from pygame import Vector2 as vec2

from pygame.typing import ColorLike, Point

# from ddframework.msgbroker import broker

import mc.config as C

from mc.launchers import mk_explosion, mk_trail_eraser
from mc.types import Comp, EntityID, Momentum, Prop, Trail
from mc.utils import play_sound


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
        ecs.set_property(eid, Prop.IS_DEAD)


def sys_explosion(dt: float,
                  eid: EntityID,
                  textures: Callable,
                  prsa: PRSA,
                  scale: LerpThing) -> None:
    if scale.finished():
        ecs.remove_entity(eid)
        return

    prsa.scale = scale()


def sys_dont_overshoot(dt: float, eid: EntityID,
                       prsa: PRSA, momentum: vec2, target: vec2) -> None:
    delta = target - prsa.pos
    dot = momentum * delta

    if not delta or delta.length() < momentum.length() and dot < 0:
        prsa.pos = target
        ecs.add_component(eid, Prop.IS_DEAD, True)


def sys_is_dead(dt: float, eid: EntityID) -> None:
    if ecs.eid_has(Comp.SHUTDOWN):
        shutdown = ecs.comp_of_eid(Comp.SHUTDOWN)
        shutdown(eid)
    ecs.remove_entity(eid)


def sys_detonate_missile(dt: float,
                         eid: EntityID,
                         prsa: PRSA,
                         trail: Trail,
                         is_dead: bool) -> None:
    mk_explosion(prsa.pos)
    mk_trail_eraser(trail)
    play_sound(cache['sounds']['explosion'], 3)


def sys_lifetime(dt: float, eid: EntityID, lifetime: Cooldown) -> None:
    """Flags entity for culling after lifetime runs out."""
    if lifetime.cold():
        ecs.add_component(eid, Prop.IS_DEAD, True)


def sys_momentum(dt: float, eid: EntityID, prsa: PRSA, momentum: Momentum) -> None:
    """Apply a static momentum to the position, a.k.a. float."""
    prsa.pos += momentum * dt


def sys_mouse(dt: float, eid: EntityID, prsa: PRSA, *, remap: Callable) -> None:
    """Apply mouse position to prsa.pos"""
    mp = remap(pygame.mouse.get_pos())
    prsa.pos = vec2(mp)


def sys_shutdown(dt: float, eid: float, is_dead: bool) -> None:
    """Call all shutdown callbacks and remove the entity"""

    if ecs.eid_has(eid, Comp.SHUTDOWN):
        callbacks = ecs.comp_of_eid(eid, Comp.SHUTDOWN)
        if isinstance(callbacks, Sequence):
            for cb in callbacks:
                cb(eid)
        else:
            callbacks(eid)

    ecs.remove_entity(eid)


def sys_target_reached(dt: float, eid: EntityID, prsa: PRSA, target: vec2) -> None:
    """Flag the entity for culling if it has reached target."""
    if prsa.pos == target:
        ecs.add_component(eid, Prop.IS_DEAD, True)


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
    """Render the current texture following the settings in prsa."""
    # FIXME unneeded?
    # tpos = round(prsa.pos.x), round(prsa.pos.y)
    # rect = texture.get_rect().scale_by(prsa.scale).move_to(center=tpos)
    rect = texture.get_rect().scale_by(prsa.scale)
    if ecs.has(eid, Comp.ANCHOR):
        anchor = ecs.comps_of_eid(Comp.ANCHOR)
        setattr(rect, anchor, prsa.pos)
    else:
        rect.center = prsa.pos

    bkp_alpha = texture.alpha

    texture.alpha = prsa.alpha  # ty: ignore
    texture.draw(dstrect=rect, angle=prsa.rotation)

    texture.alpha = bkp_alpha


def sys_texture_from_texture_list(dt: float, eid: EntityID, textures: Callable) -> None:
    """Update the current texture from an automatic image cycle."""
    ecs.add_component(eid, Comp.TEXTURE, textures())


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


def sys_update_trail(dt: float, eid: EntityID, prsa: PRSA, trail: Trail) -> None:
    previous = trail[-1][1]
    trail.append((previous, prsa.pos.copy()))


# def sys_draw_city(dt, eid, textures, is_ruined, rect):
#     sys_draw_texture(dt, eid, textures[is_ruined], rect)

# def sys_draw_texture(dt, eid, texture, rect):
#     texture.draw(dstrect=rect)

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
