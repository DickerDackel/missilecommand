from pgcooldown import remap

def to_viewport(pos, real_size, virtual_size):
    return (remap(0, real_size[0], 0, virtual_size[0], pos[0]),
            remap(0, real_size[1], 0, virtual_size[1], pos[1]))

__all__ = ['to_viewport']
