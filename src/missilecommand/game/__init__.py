import logging
logging.info(__name__)  # noqa: E402

from enum import StrEnum, auto
from itertools import chain, cycle
from random import randint, seed, shuffle
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

import missilecommand.config as C

from missilecommand.game.briefing import Briefing
from missilecommand.game.debriefing import Debriefing
from missilecommand.game.demoplayer import DemoPlayer
from missilecommand.game.incoming import Incoming
from missilecommand.game.pause import Pause
from missilecommand.game.waves import wave_iter
from missilecommand.gamestate import gs as GS
from missilecommand.highscoretable import highscoretable
from missilecommand.launchers import (mk_battery, mk_city, mk_crosshair,
                                      mk_flyer, mk_instructions, mk_missile,
                                      mk_ruin, mk_score_label, mk_smartbomb,
                                      mk_target, mk_textlabel, mk_texture)
from missilecommand.systems import (non_ecs_sys_collide_flyer_with_explosion,
                                    non_ecs_sys_collide_missile_with_battery,
                                    non_ecs_sys_collide_missile_with_city,
                                    non_ecs_sys_collide_missile_with_explosion,
                                    non_ecs_sys_collide_smartbomb_with_battery,
                                    non_ecs_sys_collide_smartbomb_with_city,
                                    non_ecs_sys_collide_smartbomb_with_explosion,
                                    non_ecs_sys_prune, sys_aim,
                                    sys_close_orphan_sound, sys_container,
                                    sys_detonate_flyer, sys_detonate_missile,
                                    sys_detonate_smartbomb,
                                    sys_dont_overshoot, sys_explosion,
                                    sys_lifetime, sys_momentum, sys_mouse,
                                    sys_shutdown, sys_target_reached,
                                    sys_draw_textlabel, sys_draw_texture,
                                    sys_smartbomb_evade, sys_textblink,
                                    sys_texture_from_texture_list,
                                    sys_trail_eraser, sys_trail,
                                    sys_update_trail,)
from missilecommand.types import Comp, EIDs, EntityID, Prop
from missilecommand.utils import (check_for_exit, cls, pause_all_sounds, play_sound, purge_entities, unpause_all_sounds)


class StatePhase(StrEnum):
    SETUP = auto()
    BRIEFING = auto()
    PLAYING = auto()
    PRE_LINGER = auto()
    LINGER = auto()
    DEBRIEFING = auto()
    GAMEOVER = auto()


class Game(GameState):
    def __init__(self, app: App, demo=False) -> None:
        self.app = app
        self.demo = demo
        self.renderer = self.app.renderer

        self.demo_player = DemoPlayer(C.ASSETS / 'demo.in')
        self.demo_walker = None

        self.mouse = None

        ecs.create_entity(EIDs.FLYER_SOUND)
        ecs.create_entity(EIDs.SMARTBOMB_SOUND)
        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

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
            StatePhase.SETUP: self.update_setup_phase,
            StatePhase.BRIEFING: self.update_briefing_phase,
            StatePhase.PLAYING: self.update_gameplay_phase,
            StatePhase.PRE_LINGER: self.update_pre_linger_phase,
            StatePhase.LINGER: self.update_linger_phase,
            StatePhase.DEBRIEFING: self.update_debriefing_phase,
            StatePhase.GAMEOVER: self.update_gameover_phase,
        }

        self.allowed_targets = None

    def reset(self, *args: Any, **kwargs: Any) -> None:
        self.mouse = self.app.logical_rect.center
        pygame.mouse.set_pos(self.app.coordinates_to_window(self.mouse))

        rect = pygame.Rect(self.app.coordinates_to_window(C.CROSSHAIR_CONSTRAINT.topleft),
                           self.app.size_to_window(C.CROSSHAIR_CONSTRAINT.size))
        self.app.window.mouse_rect = rect

        GS.reset()

        self.demo_walker = iter(self.demo_player)
        seed(a=1 if self.demo else None)
        seed(1)

        self.paused = False
        self.level = -1
        self.wave = None
        self.wave_iter = wave_iter()
        self.phase_walker = self.phases.walker()
        self.phase = next(self.phase_walker)

        GS.cities = [True] * 6

        ecs.reset()
        ecs.create_archetype(Comp.PRSA)  # for Smartbomb collisions, but useful in general
        ecs.create_archetype(Comp.PRSA, Comp.MASK)  # for Flyer collisions
        ecs.create_archetype(Comp.PRSA, Comp.MASK, Comp.SCALE)  # for Explosion collisions
        ecs.create_archetype(Comp.PRSA, Comp.TARGET, Comp.MOMENTUM)  # For smartbomb evasion

        mk_crosshair(self.app.logical_rect.center)

        msg = C.MESSAGES['game']['HIGHSCORE']
        mk_score_label(f'{highscoretable.leader.score:5d}', *msg[1:], eid=EIDs.HIGHSCORE)
        msg = C.MESSAGES['game']['SCORE']
        mk_score_label(f'{GS.score:5d}  ', msg.pos, msg.anchor, msg.color, eid=EIDs.SCORE)
        mk_textlabel('←', msg.pos, msg.anchor, msg.color, eid=EIDs.SCORE_ARROW)
        ecs.add_component(EIDs.SCORE_ARROW, Comp.COLOR_CYCLE, AutoSequence((C.COLOR.special_text, C.COLOR.background)))

        msg = C.MESSAGES['game']['BONUS CITIES']
        prsa = PRSA(pos=msg.pos, scale=(0.8, 0.8))
        mk_textlabel(f' x {GS.bonus_cities}', *msg[1:], eid=EIDs.BONUS_CITIES)
        mk_texture(cache['textures']['small-cities'][0], prsa, anchor='midright')

        self.cd_flyer = None

        def reset_cd_flyer() -> None:
            self.cd_flyer.reset()

        if self.demo:
            mk_instructions()

    def setup_wave(self) -> None:
        purge_entities(Prop.IS_BATTERY)
        purge_entities(Prop.IS_CITY)
        purge_entities(Prop.IS_EXPLOSION)
        purge_entities(Prop.IS_FLYER)
        purge_entities(Prop.IS_MISSILE)
        purge_entities(Prop.IS_SMARTBOMB)
        purge_entities(Prop.IS_SILO)
        purge_entities(Prop.IS_TARGET)

        cls(self.trail_canvas, C.COLOR.clear)

        GS.batteries = [mk_battery(i, pos)[1] for i, pos in enumerate(C.POS_BATTERIES)]

        for city, alive in enumerate(GS.cities):
            pos = C.POS_CITIES[city]
            if alive:
                mk_city(pos, eid=f'city-{city}')
            elif GS.bonus_cities > 0:
                GS.bonus_cities -= 1
                mk_city(pos, eid=f'city-{city}')
                GS.cities[city] = True
            else:
                mk_ruin(pos, eid=f'ruin-{city}')

        remaining_cities = [i for i in range(len(GS.cities)) if GS.cities[i]]
        shuffle(remaining_cities)
        target_cities = cycle((C.POS_CITIES[_] for _ in remaining_cities[0:3]))
        battery_positions = C.POS_BATTERIES
        merged = zip(target_cities, battery_positions)
        flattened = list(chain.from_iterable(merged))
        self.allowed_targets = cycle(flattened)

        self.wave = next(self.wave_iter)
        self.level += 1

        GS.score_mult = min(self.level // 2 + 1, C.MAX_SCORE_MULT)

        self.incoming_left = self.wave.missiles
        self.incoming = Incoming(C.INCOMING_SLOTS)

        self.cd_flyer = Cooldown(self.wave.flyer_cooldown)
        self.cd_flyer_shoot = Cooldown(self.wave.flyer_shoot_cooldown)

        self.smartbombs_left = self.wave.smartbombs
        self.smartbombs = Incoming(3)

    def restart(self, from_state: GameState, result: object) -> None:
        unpause_all_sounds()

    def dispatch_event(self, e: pygame.event.Event) -> None:
        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            raise StateExit

        if self.demo:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                raise StateExit(1)

            return

        self.mouse = self.app.coordinates_from_window(pygame.mouse.get_pos())

        if e.type == pygame.KEYDOWN:
            if self.phase == StatePhase.PLAYING and e.key in C.KEY_SILO_MAP:
                launchpad = C.KEY_SILO_MAP[e.key]
                self.launch_defense(launchpad, self.mouse)
            elif e.key == pygame.K_p:
                self.app.push(Pause(self.app), passthrough=StackPermissions.DRAW)
                pause_all_sounds()

    def update(self, dt: float) -> None:
        if self.paused: return
        if self.app.is_stacked(self): return

        update_fn = self.phase_handlers[self.phase]
        update_fn(dt)
        fps = self.app.clock.get_fps()
        entities = len(ecs.eidx)
        self.app.window.title = f'{self.app.title} - {fps=:.2f}  slots={len(self.incoming)}  left={self.incoming_left}  {entities=}'

    def update_setup_phase(self, dt: float) -> None:
        self.setup_wave()
        self.phase = next(self.phase_walker)

    def update_briefing_phase(self, dt: float) -> None:
        self.phase = next(self.phase_walker)
        cities = sum(GS.cities)

        self.app.push(Briefing(self.app, GS.score_mult, cities), passthrough=StackPermissions.DRAW)

    def _update_demo_mode(self):
        while True:
            try:
                demo_event = next(self.demo_walker)
            except StopIteration:
                break

            match demo_event:
                case 'NOP':
                    break
                case ['MOUSE', x, y]:
                    self.mouse = (float(x), float(y))
                case ['MISSILE', start_x, start_y, dest_x, dest_y, speed]:
                    # This is nearly duplicated from spawn_missile above, but
                    # at this point I can't be bothered to refactor that...

                    def attack_shutdown_callback(eid: EntityID) -> None:
                        self.incoming.remove(eid)

                    start = vec2(start_x, start_y)
                    target = vec2(dest_x, dest_y)
                    speed = speed

                    eid = mk_missile(start, target, speed, incoming=True,
                                     shutdown_callback=attack_shutdown_callback)
                    self.incoming.add(eid)
                    self.incoming_left -= 1
                case ['DEFENSE', launchpad]:
                    self.launch_defense(int(launchpad), self.mouse)

    def _update_game_mode(self):
        launched_this_frame = 0

        # Launch flyer if
        #     no flyer is active
        #     and the wave does have a flyer
        #     and flyer cooldown is cold
        #     and an incoming slot is free
        free_slots = self.incoming.free_slots() - 2 * len(self.smartbombs)
        if (not ecs.has(EIDs.FLYER)
                and self.wave.flyer_cooldown
                and self.cd_flyer.cold()
                and free_slots):

            def shutdown(eid: EntityID) -> None:
                self.cd_flyer.reset()
                self.incoming.remove(eid)

            self.incoming.add(mk_flyer(EIDs.FLYER, self.wave.flyer_min_height,
                                       self.wave.flyer_max_height,
                                       self.wave.flyer_shoot_cooldown,
                                       C.CONTAINER,
                                       shutdown))
            launched_this_frame += 1

        def spawn_missiles(number=1, origin=None):
            nonlocal launched_this_frame

            def attack_shutdown_callback(eid: EntityID) -> None:
                self.incoming.remove(eid)

            free_slots = self.incoming.free_slots() - 2 * len(self.smartbombs)
            to_launch = min(number,
                            free_slots,
                            self.incoming_left)

            for i in range(to_launch):
                start = vec2(origin) if origin else vec2(randint(0, self.app.logical_rect.width), -3)
                target = next(self.allowed_targets)
                speed = self.wave.missile_speed

                eid = mk_missile(start, target, speed, incoming=True,
                                 shutdown_callback=attack_shutdown_callback)
                self.incoming.add(eid)
                self.incoming_left -= 1
                launched_this_frame += 1
        # Once missiles have been launched, only launch more when the earlier
        # ones are below a given height.  Basically a delay between launches.
        may_launch = (len(self.incoming) == 0 and self.incoming_left > 0
                      or all(ecs.comp_of_eid(eid, Comp.PRSA).pos[1] > C.INCOMING_REQUIRED_HEIGHT
                             for eid in self.incoming))
        if may_launch:
            spawn_missiles(C.MAX_LAUNCHES_PER_FRAME - launched_this_frame)

        # Flyer shoots
        if (ecs.has(EIDs.FLYER)):
            prsa, cd_shoot = ecs.comps_of_eid(EIDs.FLYER, Comp.PRSA, Comp.FLYER_SHOOT_COOLDOWN)
            if cd_shoot.cold():
                cd_shoot.reset()
                spawn_missiles(randint(1, 3), origin=prsa.pos)

        # From the missile command ROM dump text:
        # So the conditions required for an ICBM to be eligible to split are:
        # * No previously-examined missile is above 159.
        # * The current missile, or a previously-examined missile, is at an
        #   altitude between 128 and 159.
        # * There must be available slots in the ICBM table, and unspent ICBMs
        #   for the wave.
        for eid in list(self.incoming):  # listify the set, since it will change
            prsa = ecs.comp_of_eid(eid, Comp.PRSA)
            free_slots = self.incoming.free_slots() - 2 * len(self.smartbombs)
            if (C.FORK_HEIGHT_RANGE[0] < prsa.pos[1] < C.FORK_HEIGHT_RANGE[1]
                and free_slots
                and self.incoming_left):
                spawn_missiles(randint(1, 3))
            else:
                break

        # Smartbombs are like missiles, but they take **2** missile slots.
        # A smartbomb may be launched if:
        # * The level actually has smartbombs and there are still some left to launch
        # * A smartbomb slot is free (max 3 on screen)
        # * 2 Missile slots are free (counting already active smartbombs as well)
        free_slots = self.incoming.free_slots() - 2 * len(self.smartbombs)
        if (C.MAX_LAUNCHES_PER_FRAME - launched_this_frame > 0
            and self.smartbombs_left
            and self.smartbombs.free_slots()
            and self.incoming.free_slots() >= 2 * (len(self.smartbombs) + 1)):

            def shutdown(eid: EntityID):
                self.smartbombs.remove(eid)

            start = vec2(randint(0, self.app.logical_rect.width), -3)
            target = next(self.allowed_targets)
            speed = self.wave.missile_speed
            eid = mk_smartbomb(start, target, speed, shutdown_callback=shutdown)
            self.smartbombs.add(eid)
            self.smartbombs_left -= 1
            launched_this_frame += 1

    def update_gameplay_phase(self, dt: float) -> None:
        # Switch to linger  if
        #   No ammunition left
        #   No city left
        #   No more incoming
        silos_left = sum(len(b) for b in GS.batteries)

        if (silos_left == 0
            or (not self.incoming and self.incoming_left <= 0
                and not self.smartbombs and self.smartbombs_left <= 0)):
            self.phase = next(self.phase_walker)
            return

        if self.demo:
            self._update_demo_mode()
        else:
            self._update_game_mode()

        ecs.add_component(EIDs.BONUS_CITIES, Comp.TEXT, f' x {GS.bonus_cities}')

        self.run_game_systems(dt)
        self.do_collisions()

    def update_pre_linger_phase(self, dt: float) -> None:
        missiles = ecs.eids_by_cids(Comp.MOMENTUM, has_properties={Prop.IS_MISSILE})
        flyers = ecs.eids_by_cids(Comp.MOMENTUM, has_properties={Prop.IS_FLYER})
        smartbombs = ecs.eids_by_cids(Comp.SPEED, has_properties={Prop.IS_SMARTBOMB})

        for eid, (momentum, ) in chain(missiles, flyers):
            momentum *= 3

        # Smartbombs are not momentum based, it's recalculated every frame
        for eid, (speed, ) in smartbombs:
            ecs.add_component(eid, Comp.SPEED, speed * 3)

        self.phase = next(self.phase_walker)

    def update_linger_phase(self, dt: float) -> None:
        # if no more missiles are flying
        #     and no defenses are flying
        #     and no flyers are flying
        #     and no explosions
        # terminate
        cities = any(GS.cities)
        missiles = len(ecs.eids_by_property(Prop.IS_MISSILE))
        flyers = len(ecs.eids_by_property(Prop.IS_FLYER))
        explosions = len(ecs.eids_by_property(Prop.IS_EXPLOSION))
        smartbombs = len(ecs.eids_by_property(Prop.IS_SMARTBOMB))

        if missiles == 0 and flyers == 0 and explosions == 0 and smartbombs == 0:
            if not cities and GS.bonus_cities == 0:
                self.phase = self.phase_walker.send(1)
            else:
                self.phase = next(self.phase_walker)
                self.app.push(Debriefing(self.app), passthrough=StackPermissions.DRAW)

        self.run_game_systems(dt)
        self.do_collisions()

    def update_debriefing_phase(self, dt: float) -> None:
        if self.app.is_stacked(self): return

        if self.demo:
            raise StateExit

        self.phase = next(self.phase_walker)

    def update_gameover_phase(self, dt: float) -> None:
        if GS.score > highscoretable.last.score:
            raise StateExit(1)

        raise StateExit

    def draw(self) -> None:
        # Make mouse work even if stackpermissions forbids update

        ecs.run_system(0, sys_mouse, Comp.PRSA,
                       mouse_pos=self.mouse,
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
        if not GS.batteries[launchpad]:
            play_sound(cache['sounds']['brzzz'])
            return

        silo = GS.batteries[launchpad].pop()
        ecs.remove_entity(silo)
        if len(GS.batteries[launchpad]) == C.LOW_AMMO_WARN_THRESHOLD:
            play_sound(cache['sounds']['low-ammo'], loops=2)

        start = C.POS_BATTERIES[launchpad]
        dest = vec2(target)
        speed = C.MISSILE_SPEEDS[launchpad]

        target_eid = ecs.create_entity()

        def cb_shutdown(eid: EntityID) -> None:
            ecs.remove_entity(target_eid)

        mk_target(target_eid, dest)
        mk_missile(start, dest, speed, cb_shutdown, incoming=False)
        play_sound(cache['sounds']['launch'])

    def run_game_systems(self, dt):
        ecs.run_system(dt, sys_momentum, Comp.PRSA, Comp.MOMENTUM)
        ecs.run_system(dt, sys_smartbomb_evade, Comp.PRSA, Comp.EVADE_FIX)
        ecs.run_system(dt, sys_aim, Comp.PRSA, Comp.TARGET, Comp.MOMENTUM, Comp.SPEED, has_properties={Prop.IS_SMARTBOMB})
        ecs.run_system(dt, sys_dont_overshoot, Comp.PRSA, Comp.MOMENTUM, Comp.TARGET)
        ecs.run_system(dt, sys_update_trail, Comp.PRSA, Comp.TRAIL)
        ecs.run_system(dt, sys_target_reached, Comp.PRSA, Comp.TARGET)
        ecs.run_system(dt, sys_trail, Comp.TRAIL, texture=self.trail_canvas)
        ecs.run_system(dt, sys_trail_eraser, Comp.TRAIL, texture=self.trail_canvas, has_properties={Prop.IS_DEAD_TRAIL})
        ecs.run_system(dt, sys_explosion, Comp.TEXTURE_LIST, Comp.PRSA, Comp.SCALE, has_properties={Prop.IS_EXPLOSION})
        ecs.run_system(dt, sys_container, Comp.PRSA, Comp.CONTAINER)
        ecs.run_system(dt, sys_lifetime, Comp.LIFETIME)
        ecs.run_system(dt, sys_close_orphan_sound, Comp.SOUND_CHANNEL, Comp.PARENT_TYPE)

        self.do_collisions()

        ecs.run_system(dt, sys_detonate_flyer, Comp.PRSA, has_properties={Prop.IS_FLYER, Prop.IS_DEAD})
        ecs.run_system(dt, sys_detonate_missile, Comp.PRSA, Comp.TRAIL, has_properties={Prop.IS_MISSILE, Prop.IS_DEAD})
        ecs.run_system(dt, sys_detonate_smartbomb, Comp.PRSA, has_properties={Prop.IS_SMARTBOMB, Prop.IS_DEAD})

        # Shutdown needs to be very last, else all the IS_DEAD filters won't trigger
        ecs.run_system(dt, sys_shutdown, Comp.SHUTDOWN, has_properties={Prop.IS_DEAD})

        non_ecs_sys_prune()

    def do_collisions(self) -> None:
        non_ecs_sys_collide_flyer_with_explosion()
        non_ecs_sys_collide_missile_with_battery()
        non_ecs_sys_collide_missile_with_city()
        non_ecs_sys_collide_missile_with_explosion()
        non_ecs_sys_collide_smartbomb_with_battery()
        non_ecs_sys_collide_smartbomb_with_city()
        non_ecs_sys_collide_smartbomb_with_explosion()

        ecs.add_component(EIDs.SCORE, Comp.TEXT, f'{GS.score:5d}  ')
        if GS.score > highscoretable.leader.score:
            ecs.add_component(EIDs.HIGHSCORE, Comp.TEXT, f'{GS.score:5d}')
