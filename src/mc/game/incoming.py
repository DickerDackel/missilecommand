from collections.abc import MutableSet

class Incoming(MutableSet):
    def __init__(self, slots, iterable=None):
        self.slots = slots
        if iterable is None:
            self.data = set()
        else:
            self.data = set(iterable)

    def __repr__(self):
        return self.data.__repr__()

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def add(self, item):
        if self.slots and len(self) >= self.slots:
            raise ValueError(f'Maximum number of entries: {self.slots}')

        self.data.add(item)

    def discard(self, item):
        self.data.discard(item)

    def free_slots(self):
        return self.slots - len(self)
