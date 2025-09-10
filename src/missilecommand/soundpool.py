import pygame

pygame.mixer.init()


class MockChannel(pygame.mixer.Channel):
    """Fake a Channel object.

    An instance of this is returned when audio is disabled in the config.

    It only implements the calls that I use in this project.
    """

    @property
    def id(self): return None

    def play(self, *args, **kwargs): return None
    def stop(self): return None
    def pause(self): return None
    def unpause(self): return None
    def set_volume(self, *args, **kwargs): return None


class SoundPool:
    DEFAULT_CHANNELS = 16

    def __init__(self, channels=None):
        self.max_channels = channels if channels is not None else self.DEFAULT_CHANNELS
        pygame.mixer.set_num_channels(self.max_channels)

        self.channels = [pygame.mixer.Channel(i) for i in range(self.max_channels)]

    def __getitem__(self, i):
        try:
            return self.channels[i]
        except IndexError:
            return MockChannel()

    def __iter__(self):
        return iter(self.channels)


soundpool = SoundPool()
