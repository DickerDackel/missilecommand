class GameState:
    def __init__(self):
        self.score = 0
        self.score_mult = 1

        self.bonus_cities = 0

        self.batteries = None
        self.cities = None

    reset = __init__


gs = GameState()
