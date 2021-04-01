from numba import jit, njit
import numba as nb

# could use numpy arrays for map, fov, navigation maps, etc.

class Position:

    #@jit("(None),(None)", nopython=True, nogil=True, cache=True)
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


class Velocity:
    #@nb.jit("void(int32,int32)", nopython=True, nogil=True)
    def __init__(self, x=0.0, y=0.0):
            self.x = x
            self.y = y

class Renderable:
    pass

class SessionId:
    #@njit
    def __init__(self, sid):
                self.sid = sid

class Person:
    #@njit
    def __init__(self, name):
                self.name = name