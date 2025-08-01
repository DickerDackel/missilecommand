from itertools import chain, cycle
from random import randint, sample

import pygame
import pygame._sdl2 as sdl2
import tinyecs as ecs

from pgcooldown import Cooldown

import ddframework.cache as cache

from ddframework.app import GameState, StateExit, StackPermissions
from ddframework.statemachine import StateMachine

import mc.config as C

from mc.components import Comp
from mc.systems import (explosion_system,
                        mouse_system,
                        move_towards_system,
                        textlabel_system,
                        texture_system,
                        textures_system,
                        trail_system,
                        trail_eraser_system)
from mc.utils import debug_grid

from mc.game.briefing import Briefing
# from mc.game.debriefing import Debriefing
from mc.entities import (mk_battery,
                         mk_crosshair,
                         mk_city,
                         mk_defense,
                         mk_target,
                         mk_textlabel)
# from mc.entities import (MissileHead,
from mc.game.pause import Pause
from mc.game.types import GamePhase
from mc.game.waves import wave_iter
# from mc.sprite import TGroup
from mc.utils import to_viewport

state_machine = StateMachine()
state_machine.add(GamePhase.SETUP, GamePhase.BRIEFING)
state_machine.add(GamePhase.BRIEFING, GamePhase.PLAYING)
state_machine.add(GamePhase.PLAYING, GamePhase.END_OF_WAVE)
state_machine.add(GamePhase.END_OF_WAVE, GamePhase.DEBRIEFING)
state_machine.add(GamePhase.DEBRIEFING, GamePhase.SETUP)


def get_cities():
    return (e for e in ecs.eids_by_property(Comp.IS_CITY))

def purge_entities(property):
    for eid in ecs.eids_by_property(property):
        ecs.remove_entity(eid)


class Game(GameState):
    def __init__(self, app):
        self.app = app
        self.renderer = self.app.renderer

        pygame.mouse.set_pos(app.logical_to_window(self.app.logical_rect.center))

        self.trail_canvas = sdl2.Texture(self.renderer, self.app.logical_rect.size, target=True)
        self.trail_canvas.blend_mode = pygame.BLENDMODE_BLEND

        # self.trails = []
        # self.attacks = TGroup()
        # self.missiles = TGroup()
        # self.targets = TGroup()
        # self.explosions = TGroup()

        self.score = None
        self.paused = None
        self.level = None

        self.wave_iter = None
        self.wave = None

        self.phase_walker = None
        self.phase = None

        self.cd_attacks = None
        self.score_mult = None
        self.to_launch = None

        self.cities = None
        self.silos = None
        self.missiles = None
        self.allowed_targets = None


    def reset(self):
        self.score = 0
        self.paused = False
        self.level = 0
        self.wave = None
        self.wave_iter = wave_iter()
        self.phase_walker = state_machine.walker()
        self.phase = next(self.phase_walker)

        self.cd_attacks = Cooldown(2, cold=True)

        ecs.reset()

        mk_crosshair()
        self.cities = [mk_city(i, pos) for i, pos in enumerate(C.POS_CITIES)]
        self.silos = [mk_battery(i, pos)[1] for i, pos in enumerate(C.POS_BATTERIES)]

        msg = C.MESSAGES['SCORE']
        mk_textlabel(f'{self.score:5d}', msg.pos, msg.anchor, msg.color, eid=msg.text)

    def setup_wave(self):
        # self.attacks.empty()
        # self.missiles.empty()
        # self.trails.clear()
        # self.targets.empty()
        # self.explosions.empty()
        # Nope!  purge_entities(Comp.IS_CITY)
        purge_entities(Comp.IS_SILO)

        for i, pos in enumerate(C.POS_BATTERIES):
            mk_battery(i, pos)

        self.cities = [e for e in get_cities()]

        self.renderer.draw_color = C.Color.clear
        self.renderer.target = self.trail_canvas
        self.renderer.clear()
        self.renderer.target = None
        self.renderer.draw_color = C.Color.background

        self.allowed_targets = cycle(a for x in (zip(self.silos, sample(self.cities, k=2))) for a in x)

        self.wave = next(self.wave_iter)
        # self.score_mult = self.level // 2 + 1
        # self.cd_attacks.reset(2)
        self.to_launch = self.wave.missiles

    def restart(self, from_state, result):
        pass

    def dispatch_event(self, e):
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

    def update(self, dt):
        if self.paused: return
        if self.app.is_stacked(self): return

        if self.phase is GamePhase.SETUP:
            self.update_setup_phase(dt)

        elif self.phase is GamePhase.BRIEFING:
            self.update_briefing_phase(dt)

        elif self.phase is GamePhase.PLAYING:
            self.update_playing_phase(dt)
        #     if self.to_launch == 0 and not self.attacks:
        #         self.phase = next(self.phase_walker)

        elif self.phase is GamePhase.END_OF_WAVE:
            self.update_playing_phase(dt)

        #     if not self.missiles and not self.attacks and not self.explosions:
        #         self.phase = next(self.phase_walker)

        elif self.phase is GamePhase.DEBRIEFING:
            self.update_debriefing_phase(dt)

        elif self.phase is GamePhase.GAMEOVER:
            ...

    def draw(self):
        debug_grid(self.app.renderer)

        # Make mouse work even if stackpermissions forbids update
        ecs.run_system(0, mouse_system, Comp.PRSA,
                       remap=self.app.window_to_logical,
                       has_properties={Comp.WANTS_MOUSE})

        ground = cache.get('ground')
        rect = ground.get_rect(midbottom=self.app.logical_rect.midbottom)
        ground.draw(dstrect=rect)

        self.trail_canvas.draw()
        ecs.run_system(0, textures_system, Comp.TEXTURES, Comp.PRSA)
        ecs.run_system(0, texture_system, Comp.TEXTURE, Comp.PRSA)

        ecs.run_system(0, textlabel_system, Comp.TEXT, Comp.PRSA, Comp.ANCHOR, Comp.COLOR)

        # self.app.renderer.draw_color = 'grey'
        # self.app.renderer.draw_rect(self.app.logical_rect)

        # ecs.run_system(0, sys_draw_city, Comp.TEXTURES, Comp.IS_RUIN, Comp.RECT)

        # ecs.run_system(0, sys_mouse, Comp.POS, Comp.RECT, Comp.TEXTURE, Comp.WANTS_MOUSE,
        #                real_size=self.app.window_rect.size,
        #                virtual_size=self.app.logical_rect.size)

    def update_setup_phase(self, dt):
        self.setup_wave()
        self.phase = next(self.phase_walker)

    def update_briefing_phase(self, dt):
        self.phase = next(self.phase_walker)
        self.app.push(Briefing(self.app, 1),
                      passthrough=StackPermissions.DRAW)

    def update_playing_phase(self, dt):
        ...

        # def launch_attack(target, speed_frames, rect, renderer, texture):
        #     start = (randint(0, rect.width), -5)
        #     speed = speed_frames
        #     mk_missile_head(start, target.pos, speed)
        #     trail = Trail(start, missile, renderer, texture)

        #     return missile, trail

        # if self.cd_attacks.cold():
        #     self.cd_attacks.reset()
        #     count = min(G.MISSILES_PER_WAVE, self.to_launch)
        #     for i in range(count):
        #         missile, trail = launch_attack(next(self.allowed_targets),
        #                                        self.wave.missile_speed,
        #                                        self.app.logical_rect,
        #                                        self.renderer,
        #                                        self.trail_canvas)
        #         self.attacks.add(missile)
        #         self.trails.append(trail)

        #     self.to_launch -= count

        ecs.run_system(dt, move_towards_system, Comp.PRSA, Comp.TARGET,
                       Comp.SPEED, Comp.TRAIL,
                       has_properties={Comp.IS_MISSILE})
        ecs.run_system(0, trail_system, Comp.TRAIL, texture=self.trail_canvas)
        ecs.run_system(0, trail_eraser_system, Comp.TRAIL,
                       texture=self.trail_canvas,
                       has_properties={Comp.IS_DEAD_TRAIL})
        ecs.run_system(0, explosion_system, Comp.TEXTURES, Comp.PRSA,
                       Comp.EXPLOSION_SCALE, has_properties={Comp.IS_EXPLOSION})

        # for o in self.attacks: o.update(dt)
        # for o in self.missiles: o.update(dt)

        # dead = [o for o in chain(self.missiles, self.attacks) if o.explode]
        # for o in dead:
        #     self.launch_explosion(o.pos)
        #     o.kill()

        # collisions = pygame.sprite.groupcollide(self.explosions, self.attacks,
        #                                         False, False,
        #                                         collided=Explosion.collidepoint)
        # for explosion, missiles in collisions.items():
        #     for m in missiles:
        #         m.explode = True

        # def pointcollide(left, right):
        #     return left.rect.collidepoint(right.pos)

        # collisions = pygame.sprite.groupcollide(self.cities, self.attacks,
        #                                         False, False,
        #                                         collided=pointcollide)
        # # FIXME
        # # for city, missiles in collisions.items():
        # #     city.ruined = True
        # #     for m in missiles:
        # #         m.explode = True

    def update_debriefing_phase(self, dt):
        self.phase = next(self.phase_walker)
        # self.app.push(Debriefing(self.app, self, self.silos, self.cities),
        #               passthrough=StackPermissions.DRAW)


    def launch_defense(self, launchpad, target):
        if not self.silos[launchpad]: return

        silo = self.silos[launchpad].pop()
        ecs.remove_entity(silo)

        speed = C.MISSILE_SPEEDS[launchpad]

        pos = C.POS_BATTERIES[launchpad]
        target_eid = mk_target(target, None)
        mk_defense(pos, target_eid, speed)

    # def try_missile_launch(self, launchpad, target):
    #     if not self.silos[launchpad].missiles: return

    #     missile = MissileHead(start, target, speed)
    #     self.targets.add(Target(target, missile))
    #     self.missiles.add(missile)
    #     self.trails.append(Trail(start, missile, self.app.renderer, self.trail_canvas))

    # def launch_explosion(self, pos):
    #     self.explosions.add(Explosion(pos))
