import logging
logging.info(__name__)  # noqa: E402

from typing import Any

import ddframework.msgbroker as broker

import mc.config as C


class Score:
    def __init__(self) -> None:
        self.score = 0
        broker.register(C.Events.ADD_SCORE, self.add)

    def reset(self, *args: Any, **kwargs: Any) -> None:
        ecs.reset()
        self.score = 0

    def add(self, value: int) -> None:
        self.score += value
