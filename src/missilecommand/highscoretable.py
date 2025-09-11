import json

from collections import UserList
from dataclasses import dataclass
from heapq import heapify, heappushpop, nlargest

from missilecommand import config as C


@dataclass(order=True)
class HighscoreRecord:
    score: int
    initials: str

    def __iter__(self):
        yield self.score
        yield self.initials


class HighscoreTable(UserList):
    INITIAL_HIGHSCORE_TABLE = [
        HighscoreRecord(7500, 'DFT'),
        HighscoreRecord(7495, 'DLS'),
        HighscoreRecord(7330, 'SRC'),
        HighscoreRecord(7250, 'RDA'),
        HighscoreRecord(7200, 'MJP'),
        HighscoreRecord(7150, 'JED'),
        HighscoreRecord(7005, 'DEW'),
        HighscoreRecord(6950, 'GJL'),
    ]

    def __init__(self, highscore_table=None):
        self.dirname = C.STATE_DIRECTORY
        self.fname = C.HIGHSCORE_FILE

        if highscore_table:
            self.data = [HighscoreRecord(*row) for row in highscore_table]
            self._save()
        elif self.fname.exists():
            with open(self.fname) as f:
                self.data = [HighscoreRecord(*row) for row in json.load(f)]
        else:
            self.data = self.INITIAL_HIGHSCORE_TABLE.copy()
            self._save()

        heapify(self.data)

    def __getitem__(self, i):
        return HighscoreRecord(*self.data[i])

    def __setitem__(self, i, item):
        if not isinstance(item, HighscoreRecord):
            item = HighscoreRecord(*item)
        self.data[i] = list(item)

    def append(self, val):
        heappushpop(self.data, val)
        self._save()

    @property
    def leader(self):
        return nlargest(1, self.data)[0]

    @property
    def last(self):
        return self.data[0]

    def _save(self):
        self.dirname.mkdir(parents=True, exist_ok=True)
        with open(self.fname, 'w') as f:
            json.dump([list(entry) for entry in self.data], f)


highscoretable = HighscoreTable()
