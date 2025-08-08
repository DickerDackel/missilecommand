import logging
logging.info(__name__)  # noqa: E402

from functools import partial
from itertools import cycle
from random import randint, sample
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
from ddframework.msgbroker import broker
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.game.types import Comp, EIDs
from mc.game.launchers import mk_battery, mk_city, mk_crosshair, mk_missile, mk_explosion, mk_flyer, mk_target, mk_trail_eraser
from mc.game.briefing import Briefing
# from mc.game.debriefing import Debriefing
from mc.game.pause import Pause
from mc.game.types import GamePhase
from mc.game.waves import wave_iter
# from mc.sprite import TGroup
from mc.launchers import mk_textlabel
from mc.systems import (sys_container, sys_explosion,
                        sys_momentum, sys_mouse, sys_move_towards,
                        sys_shutdown, sys_textlabel, sys_texture, sys_textures,
                        sys_trail_eraser, sys_trail)
from mc.types import EntityID
from mc.utils import to_viewport


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

        self.cd_incoming = None
        self.score_mult = None
        self.incoming = None

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

        self.cd_incoming = Cooldown(2, cold=True)

        ecs.reset()

        # FIXME
        self.state_label = mk_textlabel('GAME',
                                        self.app.logical_rect.topright,
                                        'topright', 'white', eid='gamestate_label')

        mk_crosshair()
        self.cities = [mk_city(i, pos) for i, pos in enumerate(C.POS_CITIES)]
        self.silos = [mk_battery(i, pos)[1] for i, pos in enumerate(C.POS_BATTERIES)]

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

        for i, pos in enumerate(C.POS_BATTERIES):
            mk_battery(i, pos)

        self.cities = [e for e in get_cities()]

        self.renderer.draw_color = C.COLOR.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()
        self.renderer.target = None
        self.renderer.draw_color = C.COLOR.background

        self.allowed_targets = cycle(a for x in (zip(self.silos, sample(self.cities, k=2))) for a in x)  # noqa: E501

        self.wave = next(self.wave_iter)
        # self.score_mult = self.level // 2 + 1
        self.cd_incoming.reset(2)
        self.incoming = self.wave.missiles
        self.cd_flyer = Cooldown(self.wave.flyer_cooldown)

    def restart(self, from_state: GameState, result: object) -> None:
        pass

    def dispatch_event(self, e: pygame.event.Event) -> None:
        self.mouse = to_viewport(pygame.mouse.get_pos(),
                                 self.app.window_rect.size,
                                 self.app.logical_rect.size)

        if (e.type == pygame.QUIT
                or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            ecs.remove_entity(self.state_label)  # FIXME
            raise StateExit(-1)
        elif e.type == pygame.KEYDOWN:
            if e.key in C.KEY_SILO_MAP:
                launchpad = C.KEY_SILO_MAP[e.key]
                self.launch_defense(launchpad, self.mouse)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)
            elif e.key == pygame.K_n:
                self.phase = next(self.phase_walker)

    def update(self, dt: float) -> None:
        if self.paused: return
        if self.app.is_stacked(self): return

        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)

    def phase_setup_update(self, dt: float) -> None:
        self.setup_wave()
        self.phase = next(self.phase_walker)

    def phase_briefing_update(self, dt: float) -> None:
        self.phase = next(self.phase_walker)
        self.app.push(Briefing(self.app, 1), passthrough=StackPermissions.DRAW)

    def phase_playing_update(self, dt: float) -> None:
        if self.incoming == 0 and not self.incoming:
            self.phase = next(self.phase_walker)
            return

        # def launch_attack(target, speed_frames, rect, renderer, texture):
        #     start = (randint(0, rect.width), -5)
        #     speed = speed_frames
        #     mk_missile_head(start, target.pos, speed)
        #     trail = Trail(start, missile, renderer, texture)

        #     return missile, trail

        def attack_shutdown_callback(eid: EntityID) -> None:
            self.incoming.remove(eid)

        if self.cd_incoming.cold():
            self.cd_incoming.reset()

            count = min(C.MISSILES_PER_WAVE, self.to_launch)
            for i in range(count):
                self.to_launch -= 1

                start = (randint(0, self.app.logical_rect.width), -16)
                target = next(self.allowed_targets).pos
                speed = self.wave.missile_speed
                eid = mk_missile(start, target, speed)
                self.incoming.add(eid)

        if (self.wave.flyer_cooldown
            and not ecs.has(EIDs.FLYER)
            and self.cd_flyer.cold()):

            def shutdown(eid: EntityID):
                self.cd_flyer.reset()

            mk_flyer(self.wave.flyer_min_height, self.wave.flyer_max_height,
                     self.wave.flyer_fire_cooldown, shutdown)

        ecs.run_system(dt, sys_move_towards, Comp.PRSA, Comp.TARGET,
                       Comp.SPEED, Comp.TRAIL,
                       has_properties={Comp.IS_MISSILE_TRAIL})
        ecs.run_system(dt, sys_trail, Comp.TRAIL, texture=self.trail_canvas)
        ecs.run_system(dt, sys_trail_eraser, Comp.TRAIL,
                       texture=self.trail_canvas,
                       has_properties={Comp.IS_DEAD_TRAIL})
        ecs.run_system(dt, sys_explosion, Comp.TEXTURES, Comp.PRSA,
                       Comp.EXPLOSION_SCALE, has_properties={Comp.IS_EXPLOSION})
        ecs.run_system(dt, sys_momentum, Comp.PRSA, Comp.MOMENTUM)
        ecs.run_system(dt, sys_container, Comp.PRSA, Comp.CONTAINER)
        ecs.run_system(dt, sys_shutdown, Comp.SHUTDOWN, has_properties={Comp.IS_DEAD})

        # for o in self.incoming: o.update(dt)
        # for o in self.missiles: o.update(dt)

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
        ecs.run_system(0, sys_textures, Comp.TEXTURES, Comp.PRSA)
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
            # FIXME play bzzzzt sound
            cache['sounds']['brzzz'].play()
            return

        silo = self.silos[launchpad].pop()
        ecs.remove_entity(silo)

        start = C.POS_BATTERIES[launchpad]
        dest = vec2(target)
        speed = C.MISSILE_SPEEDS[launchpad]

        target_eid = ecs.create_entity()

        def cb_shutdown(eid: EntityID) -> None:
            ecs.remove_entiy(eid)

        mk_target(target_eid, dest)
        mk_missile(start, dest, speed, target_eid, cb_shutdown)

        # mk_defense(pos, target_eid, speed)

    # def try_missile_launch(self, launchpad, target):
    #     if not self.silos[launchpad].missiles: return

    #     missile = MissileHead(start, target, speed)
    #     self.targets.add(Target(target, missile))
    #     self.missiles.add(missile)

    # def launch_explosion(self, pos):
    #     self.explosions.add(Explosion(pos))
