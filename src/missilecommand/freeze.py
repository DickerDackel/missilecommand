import pygame
import tinyecs as ecs

from ddframework.app import App, GameState, StateExit
from ddframework.dynamicsprite import PRSA

from missilecommand.launchers import mk_textlabel


class Freeze(GameState):
    def __init__(self, app: App) -> None:
        self.app = app
        self.labels = None

    def reset(self, *args, **kwargs):
        self.labels = []
        self.labels.append(mk_textlabel('FROZEN', self.app.logical_rect.topright, 'topright', 'white'))

    def dispatch_event(self, e: pygame.event.Event) -> None:
        # NOTE: Pause is a stacked state that falls back to the main game and
        # does not exit to the desktop.
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.teardown()
            raise StateExit(-1)

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        # Done from the ECS in the underlying game state
        pass

    def teardown(self):
        for eid in self.labels:
            ecs.remove_entity(eid)
