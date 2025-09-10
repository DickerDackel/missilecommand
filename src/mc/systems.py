import logging
logging.info(__name__)  # noqa: E402

from collections.abc import Sequence
from typing import Callable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from ddframework.autosequence import AutoSequence
from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from pgcooldown import Cooldown, LerpThing
from pygame.math import Vector2 as vec2

from pygame.typing import ColorLike, Point

# from ddframework.msgbroker import broker

import mc.config as C

from mc.gamestate import gs as GS
from mc.highscoretable import highscoretable
from mc.launchers import mk_explosion, mk_ruin, mk_trail_eraser
from mc.types import Comp, EIDs, EntityID, Momentum, Prop, Trail
from mc.utils import play_sound


def sys_aim(dt: float,
            eid: EntityID,
            prsa: PRSA,
            target: Point,
            momentum: vec2,
            speed: float, *, renderer):  # FIXME
    try:
        fix = (vec2(target) - prsa.pos).normalize() * speed
    except ValueError:
        fix = vec2()

    momentum.update(fix)

    bkp_color = renderer.draw_color
    renderer.draw_color = 'red'
    renderer.draw_line(prsa.pos, prsa.pos + momentum)
    renderer.draw_color = bkp_color


def sys_apply_scale(dt: float,
                    eid: EntityID,
                    prsa: PRSA,
                    scale: Callable) -> None:
    prsa.scale = scale()


def sys_close_orphan_sound(dt, eid, sound_channel, parent_type):
    parents = ecs.eids_by_property(parent_type)
    for p_eid in parents:
        # Parents might be found, but already dead/lingering
        if not ecs.has_property(p_eid, Prop.IS_DEAD) and not ecs.has_property(p_eid, Prop.IS_LINGERING):
            return

    sound_channel.stop()
    ecs.remove_component(eid, Comp.SOUND_CHANNEL)


def sys_colorcycle(dt: float,
                   eid: EntityID,
                   colors: AutoSequence) -> None:
    ecs.add_component(eid, Comp.COLOR, colors())


def sys_colorize(dt: float,
                 eid: EntityID,
                 texture: sdl2.Texture,
                 color: ColorLike) -> None:
    texture.color = color


def sys_container(dt: float,
                  eid: EntityID,
                  prsa: PRSA,
                  container: pygame.Rect) -> None:
    if not container.collidepoint(prsa.pos):
        ecs.add_component(eid, Prop.IS_DEAD, True)
        ecs.set_property(eid, Prop.IS_DEAD)


def sys_detonate_flyer(dt: float,
                       eid: EntityID,
                       prsa: PRSA,
                       is_dead: bool) -> None:
    mk_explosion(prsa.pos)
    play_sound(cache['sounds']['explosion'])


def sys_detonate_missile(dt: float,
                         eid: EntityID,
                         prsa: PRSA,
                         trail: Trail,
                         is_dead: bool) -> None:
    mk_explosion(prsa.pos)
    mk_trail_eraser(trail)
    play_sound(cache['sounds']['explosion'])


def sys_detonate_smartbomb(dt: float,
                           eid: EntityID,
                           prsa: PRSA,
                           is_dead: bool) -> None:
    mk_explosion(prsa.pos)
    play_sound(cache['sounds']['explosion'])


def sys_dont_overshoot(dt: float, eid: EntityID,
                       prsa: PRSA, momentum: vec2, target: vec2) -> None:
    delta = target - prsa.pos
    dot = momentum * delta

    if not delta or delta.length() < momentum.length() and dot < 0:
        prsa.pos = target
        ecs.add_component(eid, Prop.IS_DEAD, True)
        ecs.set_property(eid, Prop.IS_DEAD)


def sys_draw_textlabel(dt: float, eid: EntityID, text: str,
                       prsa: PRSA, anchor: str, color: ColorLike) -> None:
    font = cache['textures']['letters']
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


def sys_draw_texture(dt: float, eid: EntityID, texture: sdl2.Texture, prsa: PRSA) -> None:
    """Render the current texture following the settings in prsa."""
    # FIXME unneeded?
    # tpos = round(prsa.pos.x), round(prsa.pos.y)
    # rect = texture.get_rect().scale_by(prsa.scale).move_to(center=tpos)
    rect = texture.get_rect().scale_by(prsa.scale)
    try:
        anchor = ecs.comp_of_eid(eid, Comp.ANCHOR)
    except ecs.UnknownComponentError:
        anchor = 'center'

    setattr(rect, anchor, prsa.pos)

    bkp_alpha = texture.alpha

    if isinstance(prsa.scale, Sequence):
        flip_x = prsa.scale[0] < 0
        flip_y = prsa.scale[1] < 0
    else:
        flip_x = flip_y = False

    texture.alpha = prsa.alpha  # ty: ignore
    texture.draw(dstrect=rect, angle=prsa.rotation, flip_x=flip_x, flip_y=flip_y)

    texture.alpha = bkp_alpha


def sys_explosion(dt: float,
                  eid: EntityID,
                  textures: Callable,
                  prsa: PRSA,
                  scale: LerpThing) -> None:
    if scale.finished():
        ecs.remove_entity(eid)
        return

    prsa.scale = scale()


def sys_lifetime(dt: float, eid: EntityID, lifetime: Cooldown) -> None:
    """Flags entity for culling after lifetime runs out."""
    if lifetime.cold():
        ecs.add_component(eid, Prop.IS_DEAD, True)
        ecs.set_property(eid, Prop.IS_DEAD)


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


def sys_smartbomb_evade(dt, eid, prsa, evade_fix):
    sys_momentum(dt, eid, prsa, evade_fix)
    ecs.remove_component(eid, Comp.EVADE_FIX)


def sys_target_reached(dt: float, eid: EntityID, prsa: PRSA, target: vec2) -> None:
    """Flag the entity for culling if it has reached target."""
    if prsa.pos == target:
        ecs.add_component(eid, Prop.IS_DEAD, True)
        ecs.set_property(eid, Prop.IS_DEAD)


def sys_textblink(dt: float, eid: EntityID, colors: AutoSequence):
    ecs.add_component(eid, Comp.COLOR, colors())


def sys_textcurtain(dt: float, eid: EntityID, text_sequence) -> None:
    ecs.add_component(eid, Comp.TEXT, text_sequence())


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


def non_ecs_sys_collide_flyer_with_explosion():
    # There is actually only max 1 flyer at any given time, but in case
    # this changes when moving past the original...
    flyers = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, has_properties={Prop.IS_FLYER})
    explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE,
                                        has_properties={Prop.IS_EXPLOSION})
    for f_eid, (f_prsa,  f_mask) in flyers:
        if ecs.has_property(f_eid, Prop.IS_DEAD) or ecs.has_property(f_eid, Prop.IS_LINGERING):
            continue

        f_rect = f_mask.get_rect(center=f_prsa.pos)

        for e_eid, (e_prsa, e_mask, e_scale) in explosions:
            lt = e_scale()
            e_rect = e_mask.get_rect()
            scale = vec2(e_rect.size) * lt
            scaled_mask = e_mask.scale(scale)
            m_rect = scaled_mask.get_rect(center=e_prsa.pos)
            offset = vec2(m_rect.topleft) - vec2(f_rect.topleft)

            if scaled_mask.overlap(f_mask, offset) is None:
                continue

            # Don't flag it dead yet, just let it linger motionless for 1s
            # until the explosion covers it.
            ecs.set_property(f_eid, Prop.IS_LINGERING)
            ecs.add_component(f_eid, Comp.LIFETIME, Cooldown(1))
            momentum = ecs.comp_of_eid(f_eid, Comp.MOMENTUM)
            momentum *= 0

            mk_explosion(f_prsa.pos)

            is_satellite = ecs.has_property(f_eid, Prop.IS_SATELLITE)
            base_score = C.Score.SATELLITE if is_satellite else C.Score.PLANE
            prev_score = GS.score // C.BONUS_CITY_SCORE
            GS.score += GS.score_mult * base_score
            if GS.score // C.BONUS_CITY_SCORE > prev_score:
                GS.bonus_cities += 1
                play_sound(cache['sounds']['bonus-city'])

            break


def non_ecs_sys_collide_missile_with_battery():
    missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_INCOMING})
    for m_eid, (m_prsa, *_) in missiles:
        for i, battery in enumerate(GS.batteries):
            if not C.HITBOX_BATTERIES[i].collidepoint(m_prsa.pos):
                continue

            ecs.add_component(m_eid, Prop.IS_DEAD, True)
            ecs.set_property(m_eid, Prop.IS_DEAD)

            if not battery: continue

            for silo in GS.batteries[i]:
                ecs.add_component(silo, Comp.LIFETIME,
                                  Cooldown(C.EXPLOSION_DURATION))
            GS.batteries[i].clear()
            break


def non_ecs_sys_collide_missile_with_city():
    missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_INCOMING})
    for m_eid, (m_prsa, *_) in missiles:
        for i, c in enumerate(GS.cities):
            if not C.HITBOX_CITY[i].collidepoint(m_prsa.pos):
                continue

            # Explode missile, even if city is already removed
            ecs.add_component(m_eid, Prop.IS_DEAD, True)
            ecs.set_property(m_eid, Prop.IS_DEAD)
            if not c: continue

            GS.cities[i] = False
            ecs.remove_entity(f'city-{i}')
            mk_ruin(C.POS_CITIES[i], f'city-{i}')


def non_ecs_sys_collide_missile_with_explosion():
    explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE,
                                        has_properties={Prop.IS_EXPLOSION})
    missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_INCOMING})
    for m_eid, (m_prsa, *_) in missiles:
        for e_eid, (e_prsa, e_mask, e_scale) in explosions:
            e_pos = e_prsa.pos
            delta = e_pos - m_prsa.pos
            width = e_mask.get_size()[0]

            if delta.length() > e_scale() * width / 2:
                continue

            ecs.add_component(m_eid, Prop.IS_DEAD, True)
            ecs.set_property(m_eid, Prop.IS_DEAD)
            GS.score += GS.score_mult * C.Score.MISSILE
            break


def non_ecs_sys_collide_smartbomb_with_city():
    smartbombs = ecs.comps_of_archetype(Comp.PRSA, has_properties={Prop.IS_SMARTBOMB})

    for b_eid, (b_prsa,) in smartbombs:
        if ecs.has_property(b_eid, Prop.IS_DEAD):
            continue

        for i, c in enumerate(GS.cities):
            if not C.HITBOX_CITY[i].collidepoint(b_prsa.pos):
                continue

            ecs.add_component(b_eid, Prop.IS_DEAD, True)
            ecs.set_property(b_eid, Prop.IS_DEAD)
            if not c: continue

            GS.cities[i] = False
            ecs.remove_entity(f'city-{i}')
            mk_ruin(C.POS_CITIES[i], f'city-{i}')

    ecs.add_component(EIDs.SCORE, Comp.TEXT, f'{GS.score:5d}  ')
    if GS.score > highscoretable.leader[0]:
        ecs.add_component(EIDs.HIGHSCORE, Comp.TEXT, f'{GS.score:5d}')


def non_ecs_sys_collide_smartbomb_with_explosion(renderer):
    explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE,
                                        has_properties={Prop.IS_EXPLOSION})
    smartbombs = ecs.comps_of_archetype(Comp.PRSA, Comp.TARGET, Comp.MOMENTUM,
                                        has_properties={Prop.IS_SMARTBOMB})

    for b_eid, (b_prsa, b_target, b_momentum) in smartbombs:
        if ecs.has_property(b_eid, Prop.IS_DEAD):
            continue

        for e_eid, (e_prsa, e_mask, e_scale) in explosions:
            lt = e_scale()
            explosion_growing = e_scale.loops == 1
            delta = e_prsa.pos - b_prsa.pos
            dlen = delta.length()

            # explode
            if dlen <= lt * C.EXPLOSION_RADIUS:
                ecs.add_component(b_eid, Prop.IS_DEAD, True)
                ecs.set_property(b_eid, Prop.IS_DEAD)

                prev_score = GS.score // C.BONUS_CITY_SCORE
                GS.score += GS.score_mult * C.Score.SMARTBOMB
                if GS.score // C.BONUS_CITY_SCORE > prev_score:
                    GS.bonus_cities += 1
                    play_sound(cache['sounds']['bonus-city'])

            # evade
            elif explosion_growing and dlen < 1.5 * C.EXPLOSION_RADIUS:

                if delta * b_momentum < 0:
                    continue

                speed = b_momentum.length()

                if dlen < 1.25 * C.EXPLOSION_RADIUS:
                    # Just dodge towards outside of radius
                    dodge = -delta.normalize() * speed * 1.5

                else:
                    # dodge left or right
                    left_dodge = delta.rotate(90).normalize()
                    right_dodge = delta.rotate(-90).normalize()
                    # dot > 0 --> Still moving towards target
                    if b_momentum * left_dodge > 0:
                        dodge = left_dodge * speed
                    else:
                        dodge = right_dodge * speed

                ecs.add_component(b_eid, Comp.EVADE_FIX, dodge)
