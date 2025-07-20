import ddframework.msgbroker as broker

import mc.config as C


class Score:
    def __init__(self):
        self.score = 0
        broker.register(C.Events.ADD_SCORE, self.add)

    def reset(self):
        self.score = 0

    def add(self, value):
        self.score += value
