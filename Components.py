# from numba import jit, njit

# could use numpy arrays for map, fov, navigation maps, etc.

# @njit
class Position:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

# @njit
class Velocity:
    def __init__(self, x=0.0, y=0.0):
            self.x = x
            self.y = y

class Renderable:
    pass

class SessionId:
    def __init__(self, sid):
                self.sid = sid

class Person:
    def __init__(self, name):
                self.name = name