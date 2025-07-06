from types import SimpleNamespace

import pygame

from pygame import Vector2
from pgcooldown import LerpThing


class ImageCycle:
    """A descriptor class for sprite animations
    Instantiate the `image` attribute as a class attribute.  Then assign a
    tuple[list[images], delay] to it.

        class Sprite(pygame.sprite.Sprite):
            image = ImageCycle()
            def __init__(self, images, delay):
                super().__init__()
                self.image = (images, delay)

    That's all.
    """
    def __set_name__(self, obj, name):
        self.attrib = f'__ImageCycle_{name}'

    def __set__(self, obj, val):
        if isinstance(val, (tuple,list)):
            images, delay = val
        else:
            images = [val]
            delay = 1

        lt = LerpThing(0, len(images), delay, repeat=1)
        obj.__setattr__(self.attrib, SimpleNamespace(image=images, lt=lt))

    def __get__(self, obj, parent):
        if obj is None: return self

        anim = obj.__getattribute__(self.attrib)

        return anim.image[int(anim.lt())]


class ImageSequence:
    """A descriptor class for sprite animations
    Instantiate the `image` attribute as a class attribute.  Then assign a
    tuple[list[images], delay] to it.

        class Sprite(pygame.sprite.Sprite):
            image = ImageSequence()
            def __init__(self, images, delay):
                super().__init__()
                self.image = (images, delay)

    That's all.
    """
    def __set_name__(self, obj, name):
        self.attrib = f'__ImageSequence_{name}'

    def __set__(self, obj, val):
        if isinstance(val, (tuple, list)):
            images, delay = val
        else:
            images = [val]
            delay = 1

        lt = LerpThing(0, len(images), delay, repeat=0)
        obj.__setattr__(self.attrib, SimpleNamespace(image=images, lt=lt))

    def __get__(self, obj, parent):
        if obj is None: return self

        anim = obj.__getattribute__(self.attrib)
        if anim.lt.duration.cold():
            return None

        return anim.image[int(anim.lt())]


class TSprite(pygame.sprite.Sprite):
    def __init__(self, pos, image, *groups, anchor='center'):
        super().__init__(groups)
        self.pos = Vector2(pos)
        self.anchor = anchor
        if image:
            self.image = image
            self.rect = pygame.FRect(self.image.get_rect())
            setattr(self.rect, self.anchor, self.pos)

    def update(self, dt):
        setattr(self.rect, self.anchor, self.pos)

    def draw(self):
        self.image.draw(dstrect=self.rect)


class TAnimSprite(TSprite):
    image = ImageCycle()

    def __init__(self, pos, images, *groups, delay=1, anchor='center'):
        super().__init__(pos, None, *groups, anchor=anchor)
        self.image = (images, delay)
        self.rect = pygame.FRect(self.image.get_rect())
        setattr(self.rect, self.anchor, self.pos)


class TSequenceSprite(TAnimSprite):
    image = ImageSequence()

    def update(self, dt):
        if self.image is None:
            self.kill()
            return

        setattr(self.rect, self.anchor, self.pos)


class TGroup(pygame.sprite.Group):
    def draw(self, renderer):
        for s in self.sprites():
            s.draw()


__all__ = [ 'ImageCycle', 'TSprite', 'TAnimSprite', 'TGroup', ]
