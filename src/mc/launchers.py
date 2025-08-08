import tinyecs as ecs

from pygame.math import Vector2 as vec2
from pygame.typing import ColorLike, Point

from ddframework.dynamicsprite import PRSA

from mc.game.types import Comp
from mc.types import EntityID


def mk_textlabel(text: str, pos: Point, anchor: str,
                 color: ColorLike, scale: tuple[float, float] = (1, 1),
                 eid: str | None = None) -> EntityID:
    eid = ecs.create_entity(eid)

    ecs.set_property(eid, Comp.IS_TEXT)
    ecs.add_component(eid, Comp.TEXT, text)
    ecs.add_component(eid, Comp.PRSA, PRSA(vec2(pos), scale=scale))
    ecs.add_component(eid, Comp.ANCHOR, anchor)
    ecs.add_component(eid, Comp.COLOR, color)

    return eid
