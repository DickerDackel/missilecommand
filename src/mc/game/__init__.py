import logging
logging.info(__name__)  # noqa: E402

from itertools import chain, cycle
from random import randint
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

from mc.game.types import Comp, EIDs
from mc.game.launchers import (mk_battery, mk_city, mk_crosshair,
                               mk_explosion, mk_flyer, mk_missile, mk_ruin,
                               mk_target, mk_trail_eraser)
from mc.game.briefing import Briefing
# from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.types import GamePhase
from mc.game.waves import wave_iter
# from mc.sprite import TGroup
from mc.launchers import mk_textlabel
from mc.systems import (sys_container, sys_detonate_missile,
                        sys_dont_overshoot, sys_explosion, sys_momentum,
                        sys_mouse, sys_shutdown, sys_target, sys_textlabel,
                        sys_texture, sys_texture_from_texture_list,
                        sys_trail_eraser, sys_trail, sys_update_trail)
from mc.types import EntityID
from mc.utils import cls, play_sound, to_viewport


def get_cities() -> list[EntityID]:
    return (e for e in ecs.eids_by_property(Comp.IS_CITY))


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
        self.silos = None
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
        self.silos = [True] * 3

        self.cd_incoming = Cooldown(2, cold=True)

        ecs.reset()
        ecs.create_archetype(Comp.PRSA, Comp.TRAIL)
        ecs.create_archetype(Comp.PRSA, Comp.TEXTURE, Comp.EXPLOSION_SCALE)

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
        # Nope!  purge_entities(Comp.IS_CITY)
        purge_entities(Comp.IS_SILO)

        self.silos = [mk_battery(i, pos) for i, pos in enumerate(C.POS_BATTERIES)]

        for i, city in enumerate(self.cities):
            pos = C.POS_CITIES[city]
            if city:
                mk_city(f'city-{city}', pos)
            else:
                mk_ruin(f'ruin-{city}', pos)

        remaining_cities = [i for i, c in enumerate(self.cities) if c]
        for city in remaining_cities:
            pos = C.POS_CITIES[city]
            mk_city(f'city-{city}', pos)

        # remaining cities can be < 3, so cycle over it
        # batteries are always 3 at start of level
        # zip city cycle and batteries, then flatten this list to get
        #   alternating missiles and batteries
        # missile command docs say, each wave will drop on the same 6 targets
        # The number of missile drops per wave is higher than 6, so cycle over
        #   the `remaining` list
        # Due to the interval between missile launches, it won't be necessary
        #   to update this cycle with destroyed cities
        city_positions = cycle(pos for i, pos in enumerate(C.POS_CITIES) if self.cities[i])
        battery_positions = C.POS_BATTERIES
        merged = zip(city_positions, battery_positions)
        flattened = chain.from_iterable(merged)
        self.allowed_targets = cycle(flattened)

        cls(self.trail_canvas, C.COLOR.clear)

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
            elif e.key == pygame.K_SPACE:
                # FIXME
                for i in range(64):
                    x1 = randint(0, self.app.logical_rect.width)
                    x2 = randint(0, self.app.logical_rect.width)
                    mk_missile(vec2(x1, 0),
                               vec2(x2, self.app.logical_rect.bottom),
                               20,
                               incoming=True)

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

        if self.incoming_left == 0 and not self.incoming:
            self.phase = next(self.phase_walker)
            return

        def attack_shutdown_callback(eid: EntityID) -> None:
            self.incoming.remove(eid)

        if self.cd_incoming.cold():
            self.cd_incoming.reset()

            count = min(C.MISSILES_PER_WAVE, self.incoming_left)
            for i in range(count):
                self.incoming_left -= 1

                start = vec2(randint(0, self.app.logical_rect.width), -16)
                target = next(self.allowed_targets)
                speed = self.wave.missile_speed
                eid = mk_missile(start, target, speed, incoming=True)
                self.incoming.append(eid)

        if (self.wave.flyer_cooldown
            and not ecs.has(EIDs.FLYER)
            and self.cd_flyer.cold()):

            def shutdown(eid: EntityID) -> None:
                self.cd_flyer.reset()

            mk_flyer(self.wave.flyer_min_height, self.wave.flyer_max_height,
                     self.wave.flyer_fire_cooldown, shutdown)

        # All for missiles
        ecs.run_system(dt, sys_momentum, Comp.PRSA, Comp.MOMENTUM)
        ecs.run_system(dt, sys_dont_overshoot, Comp.PRSA, Comp.MOMENTUM, Comp.TARGET)
        ecs.run_system(dt, sys_update_trail, Comp.PRSA, Comp.TRAIL)
        ecs.run_system(dt, sys_target, Comp.PRSA, Comp.TARGET)
        ecs.run_system(dt, sys_detonate_missile, Comp.PRSA, Comp.TRAIL,
                       Comp.IS_DEAD)

        ecs.run_system(dt, sys_trail, Comp.TRAIL, texture=self.trail_canvas)
        ecs.run_system(dt, sys_trail_eraser, Comp.TRAIL,
                       texture=self.trail_canvas,
                       has_properties={Comp.IS_DEAD_TRAIL})

        ecs.run_system(dt, sys_explosion, Comp.TEXTURE_LIST, Comp.PRSA,
                       Comp.EXPLOSION_SCALE, has_properties={Comp.IS_EXPLOSION})

        ecs.run_system(dt, sys_container, Comp.PRSA, Comp.CONTAINER)

        ecs.run_system(dt, sys_shutdown, Comp.IS_DEAD)

        # collisions
        missiles = ecs.comps_of_archetype(Comp.PRSA, Comp.TRAIL, has_properties={Comp.IS_MISSILE, Comp.IS_INCOMING})
        explosions = ecs.comps_of_archetype(Comp.PRSA, Comp.TEXTURE, Comp.EXPLOSION_SCALE,
                                            has_properties={Comp.IS_EXPLOSION})

        killed = set()
        for e_eid, (e_prsa, e_texture, e_scale) in explosions:
            e_pos = e_prsa.pos
            for m_eid, (m_prsa, m_trail) in missiles:
                if m_eid in killed: continue
                m_pos = m_prsa.pos
                delta = e_pos - m_pos
                if delta.length() < e_scale() * e_texture.width / 2:
                    ecs.add_component(m_eid, Comp.IS_DEAD, True)
                    killed.add(m_eid)


        # dead = [o for o in chain(self.missiles, self.incoming) if o.explode]
        # for o in dead:
        #     self.launch_explosion(o.pos)
        #     o.kill()

        # collisions = pygame.sprite.groupcollide(self.explosions,
        #                                         # self.incoming,
        #                                         False, False,
        #                                         collided=Explosion.collidepoint)
        # for explosion, missiles in collisions.items():
        #     for m in missiles:
        #         m.explode = True

        # def pointcollide(left, right):
        #     return left.rect.collidepoint(right.pos)

        # collisions = pygame.sprite.groupcollide(self.cities, self.incoming,
        #                                         False, False,
        #                                         collided=pointcollide)
        # # FIXME
        # # for city, missiles in collisions.items():
        # #     city.ruined = True
        # #     for m in missiles:
        # #         m.explode = True

        #     if not self.missiles and not self.incoming and not self.explosions:
        #         self.phase = next(self.phase_walker)

    def phase_debriefing_update(self, dt: float) -> None:
        self.phase = next(self.phase_walker)
        # self.app.push(Debriefing(self.app, self, self.silos, self.cities),
        #               passthrough=StackPermissions.DRAW)

    def phase_gameover_update(self, dt: float) -> None:
        ...

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

        # self.app.renderer.draw_color = 'grey'
        # self.app.renderer.draw_rect(self.app.logical_rect)

        # ecs.run_system(0, sys_draw_city, Comp.TEXTURES, Comp.IS_RUIN, Comp.RECT)

        # ecs.run_system(0, sys_mouse, Comp.POS, Comp.RECT, Comp.TEXTURE, Comp.WANTS_MOUSE,
        #                real_size=self.app.window_rect.size,
        #                virtual_size=self.app.logical_rect.size)

    def launch_defense(self, launchpad: int, target: Point) -> None:
        if not self.silos[launchpad]:
            play_sound(cache['sounds']['brzzz'])
            return

        silo = self.silos[launchpad].pop()
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

        # mk_defense(pos, target_eid, speed)

    # def try_missile_launch(self, launchpad, target):
    #     if not self.silos[launchpad].missiles: return

    #     missile = MissileHead(start, target, speed)
    #     self.targets.add(Target(target, missile))
    #     self.missiles.add(missile)

    # def launch_explosion(self, pos):
    #     self.explosions.add(Explosion(pos))
