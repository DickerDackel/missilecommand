class GameState:
    def __init__(self):
        self.score = 0
        self.score_mult = 1

        self.bonus_cities = 0

    def reset(self):
        self.__init__()
        ...


gs = GameState()
