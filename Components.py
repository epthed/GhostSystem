from numba import jit, njit
import numba as nb
from dataclasses import dataclass, field
from typing import List

from gs_map import get_district, Map

# could use numpy arrays for map, fov, navigation maps, etc.
# use dataclasses for most things here
#@jit("(None),(None)", nopython=True, nogil=True, cache=True)
@dataclass
class Position:
    z:int = 0
    y:int = 0
    x:int = 0
    district:int = 55
    desire_z:int = None
    desire_y:int = None
    desire_x:int = None
    desire_district:int = None
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
    active_districts: List[int] = field(default_factory=list) # todo change to a tuple of

class DistrictMaps:
    def __init__(self):
        self.mapList: List(Union(None, Map)) = [None] * 100

# todo add list of entities that can see this entity to Position or Renderable
@dataclass
class Renderable:
    pass
#     Renderable: bool = True

class UpdateMap:
    pass

@dataclass
class UpdateFov:
    pass
#     UpdateFov: bool = True


@dataclass
class ConnectedPlayer:
    # stuff that only counts for players, will be separated from the character entity
    sid: str
    username: str
    charName: str = ""
    character_entity: int = 0


@dataclass
class Person:
    # sentient beings, probably differentiate from robots and ghosts later
   name: str
   fov = None  #only the results of a FoV slabs query. Map district holds the FieldOfView object
   visible_entities: List[int] = field(default_factory=list)
   is_player_controlled: bool = False