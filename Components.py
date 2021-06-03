from numba import jit, njit
import numba as nb
from dataclasses import dataclass, field
from typing import List

from gs_map import get_district, Map

# could use numpy arrays for map, fov, navigation maps, etc.
# use dataclasses for most things here
class Position:
    #@jit("(None),(None)", nopython=True, nogil=True, cache=True)
    def __init__(self, z=0.0, y=0.0, x=0.0, district=55): # address by z,y,x and district
        self.z = z
        self.y = y
        self.x = x
        self.district = district
#
# class EntityMap:
#     def __init__(self, district=55):
#         self.district = district
#         self.map = Map(district)


# class Velocity:
#     #@nb.jit("void(int32,int32)", nopython=True, nogil=True)
#     def __init__(self, x=0.0, y=0.0):
#             self.x = x
#             self.y = y

@dataclass
class ActiveDistricts:
    active_districts: List[int] = field(default_factory=list)

@dataclass
class DistrictMap:
    district: int
    map: Map

class Renderable:
    pass

class UpdateMap:
    pass

@dataclass
class Character:
    # stuff that only counts for player characters
    sid: str
    username: str

class Person:
    # sentient beings, probably differentiate from robots and ghosts later
    def __init__(self, name: str):
                self.name = name