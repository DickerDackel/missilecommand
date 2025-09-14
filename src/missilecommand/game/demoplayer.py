import pygame


class DemoPlayer:
    def __init__(self, fname):
        self.events = []
        with open(fname) as f:
            for line in [s.strip() for s in f.readlines()]:
                fields = line.split()
                tick = float(fields[0])
                command = fields[1]
                args = [float(_) for _ in fields[2:]]
                self.events.append((tick, command, args))

    def __iter__(self):
        t0 = pygame.time.get_ticks()
        idx = 0
        while True:
            if pygame.time.get_ticks() - t0 > self.events[idx][0]:
                _, command, args = self.events[idx]
                yield command, *args
                idx += 1
                if idx >= len(self.events):
                    break
            else:
                yield 'NOP'
