import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from itertools import chain, cycle
from random import randint, shuffle
from typing import Any

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pgcooldown import Cooldown
from pygame.math import Vector2 as vec2
from pygame.typing import Point

from ddframework.app import App, GameState, StateExit, StackPermissions
from ddframework.autosequence import AutoSequence
from ddframework.cache import cache
from ddframework.dynamicsprite import PRSA
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game.briefing import Briefing
from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.waves import wave_iter
from mc.highscoretable import highscoretable
from mc.launchers import (mk_battery, mk_city, mk_crosshair, mk_explosion,
                          mk_flyer, mk_missile, mk_ruin, mk_score_label,
                          mk_target, mk_textlabel, mk_texture)
from mc.systems import (sys_container, sys_detonate_missile,
                        sys_dont_overshoot, sys_explosion, sys_lifetime,
                        sys_momentum, sys_mouse, sys_shutdown,
                        sys_target_reached, sys_draw_textlabel,
                        sys_draw_texture, sys_textblink,
                        sys_texture_from_texture_list, sys_trail_eraser,
                        sys_trail, sys_update_trail)
from mc.types import Comp, EntityID, Prop
from mc.utils import (cls, play_sound, purge_entities)


class StatePhase(StrEnum):
    SETUP = auto()
    BRIEFING = auto()
    PLAYING = auto()
    PRE_LINGER = auto()
    LINGER = auto()
    DEBRIEFING = auto()
    GAMEOVER = auto()


class EIDs(StrEnum):
    BONUS_CITIES = auto()
    FLYER = auto()
    HIGHSCORE = auto()
    PLAYER = auto()
    SCORE = auto()
    SCORE_ARROW = auto()


class Game(GameState):
    def __init__(self, app: App) -> None:
        self.app = app
        self.renderer = self.app.renderer

        pygame.mouse.set_pos(app.coordinates_to_window(self.app.logical_rect.center))

        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

        self.score = None
        self.paused = None
        self.level = None

        self.wave_iter = None
        self.wave = None

        self.phases = StateMachine()
        self.phases.add(StatePhase.SETUP, StatePhase.BRIEFING)
        self.phases.add(StatePhase.BRIEFING, StatePhase.PLAYING)
        self.phases.add(StatePhase.PLAYING, StatePhase.PRE_LINGER)
        self.phases.add(StatePhase.PRE_LINGER, StatePhase.LINGER)
        self.phases.add(StatePhase.LINGER, StatePhase.DEBRIEFING, StatePhase.GAMEOVER)
        self.phases.add(StatePhase.DEBRIEFING, StatePhase.SETUP)
        self.phases.add(StatePhase.GAMEOVER, None)
        self.phase_walker = None
        self.phase = None

        self.phase_handlers = {
            StatePhase.SETUP: self.phase_setup_update,
            StatePhase.BRIEFING: self.phase_briefing_update,
            StatePhase.PLAYING: self.phase_playing_update,
            StatePhase.PRE_LINGER: self.phase_pre_linger_update,
            StatePhase.LINGER: self.phase_linger_update,
            StatePhase.DEBRIEFING: self.phase_debriefing_update,
            StatePhase.GAMEOVER: self.phase_gameover_update,
        }

        self.incoming_left = None
        self.incoming = None
        self.score_mult = None

        self.cities = None
        self.batteries = None
        self.missiles = None
        self.allowed_targets = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        rect = pygame.Rect(self.app.coordinates_to_window(C.CROSSHAIR_CONSTRAINT.topleft),
                           self.app.size_to_window(C.CROSSHAIR_CONSTRAINT.size))
        self.app.window.mouse_rect = rect

        self.score = 0
        self.paused = False
        self.level = -1
        self.wave = None
        self.wave_iter = wave_iter()
        self.phase_walker = self.phases.walker()
        self.phase = next(self.phase_walker)

        self.cities = [True] * 6
        self.batteries = [True] * 3
        self.bonus_cities = 0

        ecs.reset()
        ecs.create_archetype(Comp.PRSA, Comp.MASK)  # for Flyer collisions
        ecs.create_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE)  # for Explosion collisions

        mk_crosshair()

        msg = C.MESSAGES['game']['HIGHSCORE']
        mk_score_label(f'{highscoretable[0][0]:5d}', *msg[1:], eid=EIDs.HIGHSCORE)
        msg = C.MESSAGES['game']['SCORE']
        mk_score_label(f'{self.score:5d}  ', msg.pos, msg.anchor, msg.color, eid=EIDs.SCORE)
        mk_textlabel('←', msg.pos, msg.anchor, msg.color, eid=EIDs.SCORE_ARROW)  # FIXME eid literal
        ecs.add_component(EIDs.SCORE_ARROW, Comp.COLOR_CYCLE, AutoSequence((C.COLOR.special_text, C.COLOR.background)))

        msg = C.MESSAGES['game']['BONUS CITIES']
        prsa = PRSA(pos=msg.pos, scale=(0.8, 0.8))
        mk_textlabel(f' x {self.bonus_cities}', *msg[1:], eid=EIDs.BONUS_CITIES)
        mk_texture(cache['textures']['small-cities'][0], prsa, anchor='midright')

        self.cd_flyer = None

        def reset_cd_flyer() -> None:
            self.cd_flyer.reset()

    def setup_wave(self) -> None:
        purge_entities(Prop.IS_BATTERY)
        purge_entities(Prop.IS_CITY)
        purge_entities(Prop.IS_EXPLOSION)
        purge_entities(Prop.IS_FLYER)
        purge_entities(Prop.IS_MISSILE)
        purge_entities(Prop.IS_SILO)
        purge_entities(Prop.IS_TARGET)

        cls(self.trail_canvas, C.COLOR.clear)

        self.batteries = [mk_battery(i, pos)[1] for i, pos in enumerate(C.POS_BATTERIES)]

        for city, alive in enumerate(self.cities):
            pos = C.POS_CITIES[city]
            if alive:
                mk_city(pos, eid=f'city-{city}')
            elif self.bonus_cities > 0:
                self.bonus_cities -= 1
                mk_city(pos, eid=f'city-{city}')
                self.cities[city] = True
            else:
                mk_ruin(pos, eid=f'ruin-{city}')

        remaining_cities = [i for i in range(len(self.cities)) if self.cities[i]]
        shuffle(remaining_cities)
        target_cities = cycle((C.POS_CITIES[_] for _ in remaining_cities[0:3]))
        battery_positions = C.POS_BATTERIES
        merged = zip(target_cities, battery_positions)
        flattened = list(chain.from_iterable(merged))
        self.allowed_targets = cycle(flattened)

        self.wave = next(self.wave_iter)
        self.level += 1

        self.score_mult = min(self.level // 2 + 1, C.MAX_SCORE_MULT)

        self.incoming_left = self.wave.missiles
        self.incoming = set()

        self.cd_flyer = Cooldown(self.wave.flyer_cooldown)
        self.cd_flyer_shoot = Cooldown(self.wave.flyer_shoot_cooldown)

    def restart(self, from_state: GameState, result: object) -> None:
        if ecs.has(EIDs.FLYER):
            sound = ecs.comp_of_eid(EIDs.FLYER, Comp.SOUND)
            if sound is not None:
                play_sound(sound, loops=-1)

    def dispatch_event(self, e: pygame.event.Event) -> None:
        self.mouse = self.app.coordinates_from_window(pygame.mouse.get_pos())

        if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
                or e.type == pygame.QUIT):
            raise StateExit(-1)
        elif e.type == pygame.KEYDOWN and self.phase == StatePhase.PLAYING:
            if e.key in C.KEY_SILO_MAP:
                launchpad = C.KEY_SILO_MAP[e.key]
                self.launch_defense(launchpad, self.mouse)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)
                if ecs.has(EIDs.FLYER):
                    sound = ecs.comp_of_eid(EIDs.FLYER, Comp.SOUND)
                    if sound is not None: sound.stop()

    def update(self, dt: float) -> None:
        if self.paused: return
        if self.app.is_stacked(self): return

        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)
        fps = self.app.clock.get_fps()
        entities = len(ecs.eidx)
        self.app.window.title = f'{self.app.title} - {fps=:.2f} {entities=}  slots={len(self.incoming)}'

    def phase_setup_update(self, dt: float) -> None:
        self.setup_wave()
        self.phase = next(self.phase_walker)

    def phase_briefing_update(self, dt: float) -> None:
        self.phase = next(self.phase_walker)
        cities = sum(self.cities)

        self.app.push(Briefing(self.app, self.score_mult, cities), passthrough=StackPermissions.DRAW)

    def phase_playing_update(self, dt: float) -> None:
        # Switch to linger  if
        #   No ammunition left
        #   No city left
        #   No more incoming
        cities = any(self.cities)
        silos_left = sum(len(b) for b in self.batteries)

        if (not silos_left
            or not self.incoming and self.incoming_left <= 0):
            self.phase = next(self.phase_walker)
            return

        # Launch flyer if
        #     no flyer is active
        #     and the wave does have a flyer
        #     and flyer cooldown is cold
        #     and an incoming slot is free
        if (not ecs.has(EIDs.FLYER)
                and self.wave.flyer_cooldown
                and len(self.incoming) < C.INCOMING_SLOTS
                and self.cd_flyer.cold()):
            def shutdown(eid: EntityID) -> None:
                self.cd_flyer.reset()
                self.incoming.remove(eid)

            self.incoming.add(mk_flyer(EIDs.FLYER, self.wave.flyer_min_height,
                                       self.wave.flyer_max_height,
                                       self.wave.flyer_shoot_cooldown,
                                       self.app.logical_rect.inflate(32, 32),
                                       shutdown))

        def spawn_missiles(number=1, origin=None):
            def attack_shutdown_callback(eid: EntityID) -> None:
                self.incoming.remove(eid)

            to_launch = min(C.MAX_LAUNCHES_PER_FRAME,
                            C.INCOMING_SLOTS - len(self.incoming),
                            self.incoming_left,
                            number)

            for i in range(to_launch):
                start = vec2(origin) if origin else vec2(randint(0, self.app.logical_rect.width), -3)
                target = next(self.allowed_targets)
                speed = self.wave.missile_speed

                eid = mk_missile(start, target, speed, incoming=True,
                                 shutdown_callback=attack_shutdown_callback)
                self.incoming.add(eid)
                self.incoming_left -= 1

        may_launch = all(ecs.comp_of_eid(eid, Comp.PRSA).pos[1] > C.INCOMING_REQUIRED_HEIGHT
                         for eid in self.incoming)
        if may_launch:
            spawn_missiles(C.MAX_LAUNCHES_PER_FRAME)

        # Flyer shoots
        if (ecs.has(EIDs.FLYER)):
            prsa, cd_shoot = ecs.comps_of_eid(EIDs.FLYER, Comp.PRSA, Comp.FLYER_SHOOT_COOLDOWN)
            if cd_shoot.cold():
                cd_shoot.reset()
                spawn_missiles(randint(1, 3), origin=prsa.pos)

        # From the missile command ROM dump text:
        # So the conditions required for an ICBM to be eligible to split are:
        # * The current missile, or a previously-examined missile, is at an
        #   altitude between 128 and 159.
        # * No previously-examined missile is above 159.
        # * There must be available slots in the ICBM table, and unspent ICBMs
        #   for the wave.
        for eid in list(self.incoming):  # listify the set, since it will change
            prsa = ecs.comp_of_eid(eid, Comp.PRSA)
            # FIXME incomplete!
            if not (C.FORK_HEIGHT_RANGE[0] < prsa.pos[1] < C.FORK_HEIGHT_RANGE[1]):
                break

            spawn_missiles(randint(1, 3))

        ecs.add_component(EIDs.BONUS_CITIES, Comp.TEXT, f' x {self.bonus_cities}')

        self.run_game_systems(dt)

    def phase_pre_linger_update(self, dt: float) -> None:
        missiles = ecs.eids_by_property(Prop.IS_MISSILE)
        flyers = ecs.eids_by_property(Prop.IS_FLYER)
        for eid in chain(missiles, flyers):
            momentum = ecs.comp_of_eid(eid, Comp.MOMENTUM)
            momentum *= 2

        self.phase = next(self.phase_walker)

    def phase_linger_update(self, dt: float) -> None:
        # if no more missiles are flying
        #     and no defenses are flying
        #     and no flyers are flying
        #     and no explosions
        # terminate
        cities = any(self.cities)
        missiles = len(ecs.eids_by_property(Prop.IS_MISSILE))
        flyers = len(ecs.eids_by_property(Prop.IS_FLYER))
        explosions = len(ecs.eids_by_property(Prop.IS_EXPLOSION))

        if missiles == 0 and flyers == 0 and explosions == 0:
            if not cities and self.bonus_cities == 0:
                self.phase = self.phase_walker.send(1)
            else:
                self.phase = next(self.phase_walker)
                self.app.push(Debriefing(self.app, self, EIDs.SCORE, EIDs.HIGHSCORE, self.batteries, self.cities),
                              passthrough=StackPermissions.DRAW)

        self.run_game_systems(dt)
        self.do_collisions()

    def phase_debriefing_update(self, dt: float) -> None:
        if self.app.is_stacked(self): return

        self.phase = next(self.phase_walker)

    def phase_gameover_update(self, dt: float) -> None:
        if self.score > highscoretable[0][0]:
            raise StateExit(1, self.score)

        raise StateExit

    def draw(self) -> None:
        # Make mouse work even if stackpermissions forbids update

        ecs.run_system(0, sys_mouse, Comp.PRSA,
                       remap=self.app.coordinates_from_window,
                       has_properties={Comp.WANTS_MOUSE})

        ground = cache['textures']['ground']
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        self.trail_canvas.draw()
        ecs.run_system(0, sys_texture_from_texture_list, Comp.TEXTURE_LIST)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

        ecs.run_system(0, sys_textblink, Comp.COLOR_CYCLE)
        ecs.run_system(0, sys_draw_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def launch_defense(self, launchpad: int, target: Point) -> None:
        if not self.batteries[launchpad]:
            play_sound(cache['sounds']['brzzz'])
            return

        # FIXME
        if self.app.opts.unlimited:
            from mc.launchers import mk_silo
            silo = mk_silo(randint(1000, 999999), launchpad, C.POS_BATTERIES[launchpad])
        else:
            silo = self.batteries[launchpad].pop()
        ecs.remove_entity(silo)

        start = C.POS_BATTERIES[launchpad]
        dest = vec2(target)
        speed = C.MISSILE_SPEEDS[launchpad]

        target_eid = ecs.create_entity()

        def cb_shutdown(eid: EntityID) -> None:
            ecs.remove_entity(target_eid)

        mk_target(target_eid, dest)
        mk_missile(start, dest, speed, cb_shutdown, incoming=False)
        play_sound(cache['sounds']['launch'], 3)

    def run_game_systems(self, dt):
        ecs.run_system(dt, sys_momentum, Comp.PRSA, Comp.MOMENTUM)
        ecs.run_system(dt, sys_dont_overshoot, Comp.PRSA, Comp.MOMENTUM, Comp.TARGET)
        ecs.run_system(dt, sys_update_trail, Comp.PRSA, Comp.TRAIL)
        ecs.run_system(dt, sys_target_reached, Comp.PRSA, Comp.TARGET)
        ecs.run_system(dt, sys_detonate_missile, Comp.PRSA, Comp.TRAIL, Prop.IS_DEAD)
        ecs.run_system(dt, sys_trail, Comp.TRAIL, texture=self.trail_canvas)
        ecs.run_system(dt, sys_trail_eraser, Comp.TRAIL,
                       texture=self.trail_canvas,
                       has_properties={Prop.IS_DEAD_TRAIL})
        ecs.run_system(dt, sys_explosion, Comp.TEXTURE_LIST, Comp.PRSA,
                       Comp.SCALE, has_properties={Prop.IS_EXPLOSION})
        ecs.run_system(dt, sys_container, Comp.PRSA, Comp.CONTAINER)
        ecs.run_system(dt, sys_lifetime, Comp.LIFETIME)
        ecs.run_system(dt, sys_shutdown, Prop.IS_DEAD)

        self.do_collisions()

    def do_collisions(self) -> None:
        explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE,
                                            has_properties={Prop.IS_EXPLOSION})
        # There is actually only max 1 flyer at any given time, but in case
        # this changes when moving past the original...
        flyers = ecs.comps_of_archetype(Comp.PRSA, Comp.MASK, has_properties={Prop.IS_FLYER})
        missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_INCOMING})

        # Flyers
        for f_eid, (f_prsa,  f_mask) in flyers:
            if ecs.has_property(f_eid, Prop.IS_DEAD_FLYER):
                continue

            f_pos = f_prsa.pos
            f_rect = f_mask.get_rect(center=f_pos)

            for e_eid, (e_prsa, e_mask, e_scale) in explosions:
                lt = e_scale()
                e_rect = e_mask.get_rect()
                scale = vec2(e_rect.size) * lt
                scaled_mask = e_mask.scale(scale)
                m_rect = scaled_mask.get_rect(center=e_prsa.pos)

                offset = vec2(m_rect.topleft) - vec2(f_rect.topleft)

                if scaled_mask.overlap(f_mask, offset) is None:
                    continue

                sound = ecs.comp_of_eid(f_eid, Comp.SOUND)
                if sound is not None: sound.stop()

                ecs.set_property(f_eid, Prop.IS_DEAD_FLYER)
                ecs.add_component(f_eid, Comp.LIFETIME, Cooldown(1))

                momentum = ecs.comp_of_eid(f_eid, Comp.MOMENTUM)
                momentum *= 0

                mk_explosion(f_pos)

                is_satellite = ecs.has_property(f_eid, Prop.IS_SATELLITE)
                base_score = C.Score.SATELLITE if is_satellite else C.Score.PLANE
                prev_score = self.score // C.BONUS_CITY_SCORE
                self.score += self.score_mult * base_score
                if self.score // C.BONUS_CITY_SCORE > prev_score:
                    self.bonus_cities += 1
                    play_sound(cache['sounds']['bonus-city'])

                break

        # Missiles
        for m_eid, (m_prsa, *_) in missiles:
            m_pos = m_prsa.pos

            # missile vs. explosions
            for e_eid, (e_prsa, e_mask, e_scale) in explosions:
                e_pos = e_prsa.pos
                delta = e_pos - m_pos
                width = e_mask.get_size()[0]

                if delta.length() > e_scale() * width / 2:
                    continue

                ecs.add_component(m_eid, Prop.IS_DEAD, True)
                self.score += self.score_mult * C.Score.MISSILE
                break

            # missile vs. cities
            for i, c in enumerate(self.cities):
                if not c: continue

                if not C.HITBOX_CITY[i].collidepoint(m_pos):
                    continue

                ecs.add_component(m_eid, Prop.IS_DEAD, True)
                self.cities[i] = False
                ecs.remove_entity(f'city-{i}')
                mk_ruin(C.POS_CITIES[i], f'city-{i}')

            # missile vs. batteries
            for i, battery in enumerate(self.batteries):
                if not battery: continue

                if not C.HITBOX_BATTERIES[i].collidepoint(m_pos):
                    continue

                for silo in self.batteries[i]:
                    ecs.add_component(m_eid, Prop.IS_DEAD, True)
                    ecs.add_component(silo, Comp.LIFETIME,
                                      Cooldown(C.EXPLOSION_DURATION))
                self.batteries[i].clear()
                break

        ecs.add_component(EIDs.SCORE, Comp.TEXT, f'{self.score:5d}  ')
        if self.score > highscoretable[0][0]:
            ecs.add_component(EIDs.HIGHSCORE, Comp.TEXT, f'{self.score:5d}')
