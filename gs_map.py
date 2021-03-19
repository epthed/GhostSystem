import numpy as np


class Tile:
    def __init__(self, transparent=True, walkable=False, structure=0, spatial=False):
        # self.roof = True # put back in for 3d
        self.transparent = transparent
        self.walkable = walkable
        self.structure = structure
        self.spatial = spatial

    def __str__(self):  # the standard print
        return str(self.spatial)

    def __repr__(self):  # the debug print
        return str(int(self.spatial))


class Map:
    def __init__(self, y=10, x=10, z=2):
        self._array = [[Tile() for col in range(y)] for col in range(x)]  # for row in range(z)] # put back for 3d

    @property
    def transparent(self) -> np.ndarray:
        buffer = self.__buffer[:, :, 0]
        return buffer.T if self._order == "F" else buffer

    @property
    def walkable(self) -> np.ndarray:
        buffer = self.__buffer[:, :, 1]
        return buffer.T if self._order == "F" else buffer

    @property
    def fov(self) -> np.ndarray:
        buffer = self.__buffer[:, :, 2]
        return buffer.T if self._order == "F" else buffer
