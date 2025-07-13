import ddframework.msgbroker as broker

import mc.globals as G


class Score:
    def __init__(self):
        self.score = 0
        broker.register(G.Events.ADD_SCORE, self.add)

    def reset(self):
        self.score = 0

    def add(self, value):
        self.score += value
