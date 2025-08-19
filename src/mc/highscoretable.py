from collections import UserList
from heapq import heapify, heappushpop
from typing import NamedTuple


class HighscoreEntry(NamedTuple):
    score: int
    initials: str


class HighscoreTable(UserList):
    INITIAL_HIGHSCORE_TABLE = [
        (7500, 'DFT'),
        (7495, 'DLS'),
        (7330, 'SRC'),
        (7250, 'RDA'),
        (7200, 'MJP'),
        (7150, 'JED'),
        (7005, 'DEW'),
        (6950, 'GJL'),
    ]

    def __init__(self, highscore_table=None):
        if highscore_table:
            self.data = highscore_table.copy()
        else:
            self.data = self.INITIAL_HIGHSCORE_TABLE.copy()

        heapify(self.data)

    def append(self, val):
        heappushpop(self.hstable, val)


highscoretable = HighscoreTable()
