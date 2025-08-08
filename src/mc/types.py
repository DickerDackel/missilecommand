import logging
logging.info(__name__)  # noqa: E402

from typing import Hashable

import pygame

from pygame.math import Vector2 as vec2
from pygame.typing import Point

Container = pygame.Rect
EntityID = Hashable
Momentum = vec2
Trail = list[tuple[Point, Point]]
