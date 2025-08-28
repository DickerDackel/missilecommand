import json

from collections import UserList
from heapq import heapify, heappushpop, nlargest
from typing import NamedTuple

from mc import config as C


class HighscoreEntry(NamedTuple):
    score: int
    initials: str


class HighscoreTable(UserList):
    INITIAL_HIGHSCORE_TABLE = [
        [7500, 'DFT'],
        [7495, 'DLS'],
        [7330, 'SRC'],
        [7250, 'RDA'],
        [7200, 'MJP'],
        [7150, 'JED'],
        [7005, 'DEW'],
        [6950, 'GJL'],
    ]

    def __init__(self, highscore_table=None):
        self.dirname = C.STATE_DIRECTORY
        self.fname = C.HIGHSCORE_FILE

        if highscore_table:
            self.data = highscore_table.copy()
            self.save()
        elif self.fname.exists():
            with open(self.fname) as f:
                self.data = json.load(f)
        else:
            self.data = self.INITIAL_HIGHSCORE_TABLE.copy()
            self._save()

        heapify(self.data)

    def append(self, val):
        heappushpop(self.data, val)
        self._save()

    @property
    def leader(self):
        return nlargest(1, self.data)[0]

    def _save(self):
        self.dirname.mkdir(parents=True, exist_ok=True)
        with open(self.fname, 'w') as f:
            json.dump(self.data, f)


highscoretable = HighscoreTable()
