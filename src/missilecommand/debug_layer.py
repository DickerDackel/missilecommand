import missilecommand.config as C
from ddframework.app import GameState, StackPermissions
from ddframework.gridlayout import debug_grid


class DebugLayer(GameState):
    def __init__(self, app, walker):
        self.app = app
        self.renderer = self.app.renderer
        self.walker = walker

    def reset(self, *args, **kwargs):
        self.app.push(self.walker, passthrough=StackPermissions.DRAW)

    def update(self, dt):
        pass

    def draw(self):
        self.renderer.draw_color = C.COLOR.background
        self.renderer.clear()
        debug_grid(self.renderer, C.GRID, 'grey20')
