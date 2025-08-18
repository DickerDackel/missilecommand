import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from functools import partial
from itertools import chain, cycle
from random import randint, shuffle
from typing import Any

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pgcooldown import Cooldown
from pyfiglet import figlet_format
from pygame.math import Vector2 as vec2
from pygame.typing import Point

from ddframework.app import App, GameState, StateExit, StackPermissions
from ddframework.cache import cache
from ddframework.gridlayout import debug_grid
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game.briefing import Briefing
from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.waves import wave_iter
from mc.launchers import (mk_battery, mk_city, mk_crosshair, mk_explosion,
                          mk_flyer, mk_missile, mk_ruin, mk_score_label,
                          mk_target)
from mc.systems import (sys_container, sys_detonate_missile,
                        sys_dont_overshoot, sys_explosion, sys_lifetime,
                        sys_momentum, sys_mouse, sys_shutdown,
                        sys_target_reached, sys_textlabel, sys_draw_texture,
                        sys_texture_from_texture_list, sys_trail_eraser,
                        sys_trail, sys_update_trail)
from mc.types import Comp, EntityID, Prop
from mc.utils import (cls, constraint_mouse, debug_rect, play_sound,
                      purge_entities, to_viewport)


class StatePhase(StrEnum):
    SETUP = auto()
    BRIEFING = auto()
    PLAYING = auto()
    LINGER = auto()
    DEBRIEFING = auto()
    GAMEOVER = auto()


class EIDs(StrEnum):
    FLYER = auto()
    PLAYER = auto()
    SCORE = auto()


class Game(GameState):
    def __init__(self, app: App) -> None:
        self.app = app
        self.renderer = self.app.renderer

        pygame.mouse.set_pos(app.logical_to_window(self.app.logical_rect.center))

        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

        # self.incoming = TGroup()
        # self.missiles = TGroup()
        # self.targets = TGroup()
        # self.explosions = TGroup()

        self.score = None
        self.paused = None
        self.level = None

        self.wave_iter = None
        self.wave = None

        self.phases = StateMachine()
        self.phases.add(StatePhase.SETUP, StatePhase.BRIEFING)
        self.phases.add(StatePhase.BRIEFING, StatePhase.PLAYING)
        self.phases.add(StatePhase.PLAYING, StatePhase.LINGER)
        self.phases.add(StatePhase.LINGER, StatePhase.DEBRIEFING, StatePhase.GAMEOVER)
        self.phases.add(StatePhase.DEBRIEFING, StatePhase.SETUP)
        self.phases.add(StatePhase.GAMEOVER, None)
        self.phase_walker = None
        self.phase = None

        self.phase_handlers = {
            StatePhase.SETUP: self.phase_setup_update,
            StatePhase.BRIEFING: self.phase_briefing_update,
            StatePhase.PLAYING: self.phase_playing_update,
            StatePhase.LINGER: self.phase_linger_update,
            StatePhase.DEBRIEFING: self.phase_debriefing_update,
            StatePhase.GAMEOVER: self.phase_gameover_update,
        }

        self.incoming_left = None
        self.cd_incoming = None
        self.incoming = None
        self.score_mult = None

        self.cities = None
        self.batteries = None
        self.missiles = None
        self.allowed_targets = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        self.score = 0
        self.paused = False
        self.level = -1
        self.wave = None
        self.wave_iter = wave_iter()
        self.phase_walker = self.phases.walker()
        self.phase = next(self.phase_walker)

        self.cities = [True] * 6
        self.batteries = [True] * 3

        self.cd_incoming = Cooldown(2, cold=True)

        ecs.reset()
        ecs.create_archetype(Comp.PRSA, Comp.MASK)  # for Flyer collisions
        ecs.create_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE)  # for Explosion collisions

        mk_crosshair()

        msg = C.MESSAGES['SCORE']
        mk_score_label(f'{self.score:5d}', msg.pos, msg.anchor, msg.color, eid=EIDs.SCORE)

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

        self.batteries = [mk_battery(i, pos) for i, pos in enumerate(C.POS_BATTERIES)]

        for city, alive in enumerate(self.cities):
            pos = C.POS_CITIES[city]
            if alive:
                mk_city(f'city-{city}', pos)
            else:
                mk_ruin(f'ruin-{city}', pos)

        remaining_cities = [i for i in range(len(self.cities)) if self.cities[i]]
        shuffle(remaining_cities)
        target_cities = cycle((C.POS_CITIES[_] for _ in remaining_cities[0:3]))
        battery_positions = C.POS_BATTERIES
        merged = zip(target_cities, battery_positions)
        flattened = list(chain.from_iterable(merged))
        self.allowed_targets = cycle(flattened)

        self.wave = next(self.wave_iter)
        self.level += 1

        self.score_mult = self.level // 2 + 1

        self.incoming_left = self.wave.missiles
        self.incoming = []

        self.cd_incoming.reset(2)
        self.cd_flyer = Cooldown(self.wave.flyer_cooldown)

    def restart(self, from_state: GameState, result: object) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        self.mouse = to_viewport(pygame.mouse.get_pos(),
                                 self.app.window_rect.size,
                                 self.app.logical_rect.size)

        if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
                or e.type == pygame.QUIT):
            raise StateExit(-1)
        elif e.type == pygame.KEYDOWN and self.phase == StatePhase.PLAYING:
            if e.key in C.KEY_SILO_MAP:
                launchpad = C.KEY_SILO_MAP[e.key]
                self.launch_defense(launchpad, self.mouse)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)

    def update(self, dt: float) -> None:
        if self.paused: return
        if self.app.is_stacked(self): return

        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)
        fps = self.app.clock.get_fps()
        entities = len(ecs.eidx)
        self.app.window.title = f'{self.app.title} - {fps=:.2f} {entities=}'

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
        incoming = len(ecs.eids_by_property(Prop.IS_INCOMING))
        flyers = len(ecs.eids_by_property(Prop.IS_FLYER))

        if not cities:
            self.phase = next(self.phase_walker)
            return

        if not silos_left:
            self.phase = next(self.phase_walker)
            return

        if incoming == 0 and self.incoming_left == 0 and flyers == 0:
            self.phase = next(self.phase_walker)
            return

        if self.cd_incoming.cold():
            self.cd_incoming.reset()
            self.launch_incoming_wave()

        if (self.wave.flyer_cooldown
            and not ecs.has(EIDs.FLYER)
            and self.cd_flyer.cold()):

            def shutdown(eid: EntityID) -> None:
                self.cd_flyer.reset()

            mk_flyer(EIDs.FLYER, self.wave.flyer_min_height, self.wave.flyer_max_height,
                     self.wave.flyer_fire_cooldown, self.app.logical_rect.inflate(32, 32),
                     shutdown)

        self.run_game_systems(dt)

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
            if not cities:
                self.phase = self.phase_walker.send(1)
            else:
                self.phase = next(self.phase_walker)
                self.app.push(Debriefing(self.app, self, EIDs.SCORE, self.batteries, self.cities),
                              passthrough=StackPermissions.DRAW)

        self.run_game_systems(dt)
        self.do_collisions()

    def phase_debriefing_update(self, dt: float) -> None:
        if self.app.is_stacked(self): return

        self.phase = next(self.phase_walker)

    def phase_gameover_update(self, dt: float) -> None:
        raise StateExit

    def draw(self) -> None:
        debug_grid(self.app.renderer, C.GRID)

        # Make mouse work even if stackpermissions forbids update

        ecs.run_system(0, sys_mouse, Comp.PRSA,
                       remap=self.app.window_to_logical,
                       has_properties={Comp.WANTS_MOUSE})

        ground = cache['textures']['ground']
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        self.trail_canvas.draw()
        ecs.run_system(0, sys_texture_from_texture_list, Comp.TEXTURE_LIST)
        ecs.run_system(0, sys_draw_texture, Comp.TEXTURE, Comp.PRSA)

        ecs.run_system(0, sys_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

    def launch_defense(self, launchpad: int, target: Point) -> None:
        if not self.batteries[launchpad]:
            play_sound(cache['sounds']['brzzz'])
            return

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

    def launch_incoming_wave(self) -> None:
        def attack_shutdown_callback(eid: EntityID) -> None:
            self.incoming.remove(eid)

        count = min(C.MISSILES_PER_WAVE, self.incoming_left)
        for i in range(count):
            self.incoming_left -= 1

            start = vec2(randint(0, self.app.logical_rect.width), -16)
            target = next(self.allowed_targets)
            speed = self.wave.missile_speed
            # speed = 200  # FIXME
            eid = mk_missile(start, target, speed, incoming=True,
                             shutdown_callback=attack_shutdown_callback)
            self.incoming.append(eid)

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

        for f_eid, (f_prsa,  f_mask) in flyers:
            if ecs.has_property(f_eid, Prop.IS_DEAD_FLYER):
                continue

            f_pos = f_prsa.pos

            for e_eid, (e_prsa, e_mask, e_scale) in explosions:
                e_pos = e_prsa.pos
                offset = e_pos - f_pos

                scale = e_scale()
                size = vec2(e_mask.get_size())
                scaled_mask = e_mask.scale(size * scale)

                if f_mask.overlap(scaled_mask, offset) is None:
                    continue

                sound = ecs.comp_of_eid(f_eid, Comp.SOUND)
                ecs.remove_component(f_eid, Comp.SOUND)
                sound.stop()

                ecs.set_property(f_eid, Prop.IS_DEAD_FLYER)
                ecs.add_component(f_eid, Comp.LIFETIME, Cooldown(1))
                ecs.remove_component(f_eid, Comp.MOMENTUM)

                mk_explosion(f_pos)

                is_satellite = ecs.has_property(f_eid, Prop.IS_SATELLITE)
                base_score = C.Score.SATELLITE if is_satellite else C.Score.PLANE
                self.score += self.score_mult * base_score

                break

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
                mk_ruin(f'city-{i}', C.POS_CITIES[i])

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

        ecs.add_component(EIDs.SCORE, Comp.TEXT, str(self.score))
