import logging
logging.info(__name__)  # noqa: E402

from itertools import chain, cycle
from random import randint, shuffle
from typing import Any, Hashable

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pgcooldown import Cooldown
from pygame import Vector2 as vec2
from pygame.typing import Point

from ddframework.app import App, GameState, StateExit, StackPermissions
from ddframework.cache import cache
from ddframework.gridlayout import debug_grid
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game.briefing import Briefing
# from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.types import EIDs, GamePhase
from mc.game.waves import wave_iter
# from mc.sprite import TGroup
from mc.launchers import (mk_battery, mk_city, mk_crosshair, mk_flyer,
                          mk_missile, mk_ruin, mk_target, mk_textlabel,
                          mk_trail_eraser)
from mc.systems import (sys_container, sys_detonate_missile,
                        sys_dont_overshoot, sys_explosion, sys_lifetime,
                        sys_momentum, sys_mouse, sys_shutdown,
                        sys_target_reached, sys_textlabel, sys_texture,
                        sys_texture_from_texture_list, sys_trail_eraser,
                        sys_trail, sys_update_trail)
from mc.game.types import EIDs
from mc.types import Comp, EntityID, Prop
from mc.utils import cls, play_sound, to_viewport


def get_cities() -> list[EntityID]:
    return (e for e in ecs.eids_by_property(Prop.IS_CITY))


def purge_entities(property: Hashable) -> None:
    for eid in ecs.eids_by_property(property):
        ecs.remove_entity(eid)


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
        self.phases.add(GamePhase.SETUP, GamePhase.BRIEFING)
        self.phases.add(GamePhase.BRIEFING, GamePhase.PLAYING)
        self.phases.add(GamePhase.PLAYING, GamePhase.END_OF_WAVE, GamePhase.GAMEOVER)
        self.phases.add(GamePhase.END_OF_WAVE, GamePhase.DEBRIEFING)
        self.phases.add(GamePhase.DEBRIEFING, GamePhase.SETUP)
        self.phases.add(GamePhase.GAMEOVER, None)
        self.phase_walker = None
        self.phase = None

        self.phase_handlers = {
            GamePhase.SETUP: self.phase_setup_update,
            GamePhase.BRIEFING: self.phase_briefing_update,
            GamePhase.PLAYING: self.phase_playing_update,
            GamePhase.END_OF_WAVE: self.phase_playing_update,
            GamePhase.DEBRIEFING: self.phase_debriefing_update,
            GamePhase.GAMEOVER: self.phase_gameover_update,
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
        self.level = 0
        self.wave = None
        self.wave_iter = wave_iter()
        self.phase_walker = self.phases.walker()
        self.phase = next(self.phase_walker)

        self.cities = [True] * 6
        self.batteries = [True] * 3

        self.cd_incoming = Cooldown(2, cold=True)

        ecs.reset()
        ecs.create_archetype(Comp.PRSA)
        ecs.create_archetype(Comp.PRSA, Comp.TEXTURE, Comp.SCALE)

        mk_crosshair()

        msg = C.MESSAGES['SCORE']
        mk_textlabel(f'{self.score:5d}', msg.pos, msg.anchor, msg.color, eid=msg.text)

        self.cd_flyer = None

        def reset_cd_flyer() -> None:
            self.cd_flyer.reset()

    def setup_wave(self) -> None:
        # self.incoming.empty()
        # self.missiles.empty()
        # self.targets.empty()
        # self.explosions.empty()
        # Nope!  purge_entities(Prop.IS_CITY)
        purge_entities(Prop.IS_SILO)

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

        self.score_mult = self.level // 2 + 1

        self.wave = next(self.wave_iter)

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

        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            raise StateExit(-1)
        elif e.type == pygame.KEYDOWN:
            if e.key in C.KEY_SILO_MAP:
                launchpad = C.KEY_SILO_MAP[e.key]
                self.launch_defense(launchpad, self.mouse)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)
            elif e.key == pygame.K_n:
                self.phase = next(self.phase_walker)
            elif e.key == pygame.K_d:
                from pprint import pprint
                pprint(ecs.eidx)
                pprint(ecs.cidx)
                pprint(ecs.archetype)
                pprint(ecs.plist)
            elif e.key == pygame.K_x:
                raise StateExit(-1)

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
        self.app.push(Briefing(self.app, 1), passthrough=StackPermissions.DRAW)

    def phase_playing_update(self, dt: float) -> None:
        if not any(self.cities):
            self.phase = self.phase_walker.send(1)
            return

        explosions = ecs.eids_by_property(Prop.IS_EXPLOSION)
        incoming = ecs.eids_by_property(Prop.IS_INCOMING)
        if self.incoming_left == 0 and len(incoming) == 0 and len(explosions) == 0:
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
                     self.wave.flyer_fire_cooldown, self.app.logical_rect,
                     shutdown)

        # All for missiles
        ecs.run_system(dt, sys_momentum, Comp.PRSA, Comp.MOMENTUM)
        ecs.run_system(dt, sys_dont_overshoot, Comp.PRSA, Comp.MOMENTUM, Comp.TARGET)
        ecs.run_system(dt, sys_update_trail, Comp.PRSA, Comp.TRAIL)
        ecs.run_system(dt, sys_target_reached, Comp.PRSA, Comp.TARGET)
        ecs.run_system(dt, sys_detonate_missile, Comp.PRSA, Comp.TRAIL,
                       Prop.IS_DEAD)

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

    def do_collisions(self):
        # collisions
        missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_INCOMING})
        killed = set()
        for m_eid, (m_prsa, *_) in missiles:
            m_pos = m_prsa.pos

            def kill_missile(m_eid):
                ecs.add_component(m_eid, Prop.IS_DEAD, True)
                killed.add(m_eid)

            explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.TEXTURE, Comp.SCALE,
                                                has_properties={Prop.IS_EXPLOSION})
            # missile vs. explosions
            for e_eid, (e_prsa, e_texture, e_scale) in explosions:
                if m_eid in killed: continue

                e_pos = e_prsa.pos
                delta = e_pos - m_pos
                if delta.length() < e_scale() * e_texture.width / 2:
                    kill_missile(m_eid)

            # missile vs. cities
            for i, c in enumerate(self.cities):
                if not c: continue

                if C.HITBOX_CITY[i].collidepoint(m_pos):
                    kill_missile(m_eid)
                    self.cities[i] = False
                    ecs.remove_entity(f'city-{i}')
                    mk_ruin(f'city-{i}', C.POS_CITIES[i])

            # missile vs. batteries
            for i, battery in enumerate(self.batteries):
                if not battery:
                    continue

                if C.HITBOX_BATTERIES[i].collidepoint(m_pos):
                    killed.add(m_eid)

                    for silo in self.batteries[i]:
                        kill_missile(m_eid)
                        ecs.add_component(silo, Comp.LIFETIME,
                                          Cooldown(C.EXPLOSION_DURATION))
                    self.batteries[i].clear()

    def phase_debriefing_update(self, dt: float) -> None:
        self.phase = next(self.phase_walker)
        # self.app.push(Debriefing(self.app, self, self.batteries, self.cities),
        #               passthrough=StackPermissions.DRAW)

    def phase_gameover_update(self, dt: float) -> None:
        raise StateExit

    def draw(self) -> None:
        debug_grid(self.app.renderer, C.GRID)

        # Make mouse work even if stackpermissions forbids update
        ecs.run_system(0, sys_mouse, Comp.PRSA,
                       remap=self.app.window_to_logical,
                       has_properties={Comp.WANTS_MOUSE})

        ground = cache['ground']
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        self.trail_canvas.draw()
        ecs.run_system(0, sys_texture_from_texture_list, Comp.TEXTURE_LIST)
        ecs.run_system(0, sys_texture, Comp.TEXTURE, Comp.PRSA)

        ecs.run_system(0, sys_textlabel, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

        renderer = self.app.renderer
        for b in C.HITBOX_BATTERIES:
            bkp_color = renderer.draw_color
            renderer.draw_color = 'red'
            renderer.draw_rect(b)
            renderer.draw_color = bkp_color

        # self.app.renderer.draw_color = 'grey'
        # self.app.renderer.draw_rect(self.app.logical_rect)

        # ecs.run_system(0, sys_draw_city, Comp.TEXTURES, Prop.IS_RUIN, Comp.RECT)

        # ecs.run_system(0, sys_mouse, Comp.POS, Comp.RECT, Comp.TEXTURE, Comp.WANTS_MOUSE,
        #                real_size=self.app.window_rect.size,
        #                virtual_size=self.app.logical_rect.size)

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
        count = min(C.MISSILES_PER_WAVE, self.incoming_left)

        def attack_shutdown_callback(eid: EntityID) -> None:
            self.incoming.remove(eid)

        for i in range(count):
            self.incoming_left -= 1

            start = vec2(randint(0, self.app.logical_rect.width), -16)
            target = next(self.allowed_targets)
            speed = self.wave.missile_speed
            speed = 200
            eid = mk_missile(start, target, speed, incoming=True,
                             shutdown_callback=attack_shutdown_callback)
            self.incoming.append(eid)

        # mk_defense(pos, target_eid, speed)

    # def try_missile_launch(self, launchpad, target):
    #     if not self.batteries[launchpad].missiles: return

    #     missile = MissileHead(start, target, speed)
    #     self.targets.add(Target(target, missile))
    #     self.missiles.add(missile)

    # def launch_explosion(self, pos):
    #     self.explosions.add(Explosion(pos))
