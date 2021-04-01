import numpy as np


class Slab:
    # this is the generic class for walls, floors, ceilings that are thin. Opaque true = can't see through
    def __init__(self, opaque=False, blocking=False, structure=0):
        self.opaque = opaque
        self.blocking = blocking
        self.structure = structure


class Tile:
    def __init__(self, opaque=False, blocking=False, structure=0, east=Slab(), north=Slab(),
                 floor=Slab(opaque=True, blocking=True), fluid="air"):
        # define only East North and Floor. Put the rest of the 3d grid together and all 6 sides are covered.
        # split them into a binary representation, bit 1 is EastBlocking, bit 2 is EastTransparent etc. then store the
        # resulting number in a numpy array for fastness in FoV/pathing calculations
        self.opaque = opaque  # these are only for if the entire 1m volume is opaque/blocking
        self.blocking = blocking
        self.structure = structure
        self.fluid = fluid  # what is filling the tile. Water, air, smoke, plasma? string for now, will be a class
        self.east = east
        self.north = north
        self.floor = floor
        self.binarymaskarray = 0
        self.calc_binarymaskarray()

    def __str__(self):  # the standard print
        return str(self.fluid)

    def __repr__(self):  # the debug print
        return str(self.fluid)

    def calc_binarymaskarray(self):
        output = 0
        if self.east.opaque: output += 2 ** 0
        if self.east.blocking: output += 2 ** 1
        if self.north.opaque: output += 2 ** 2
        if self.north.blocking: output += 2 ** 3
        if self.floor.opaque: output += 2 ** 4
        if self.floor.blocking: output += 2 ** 5
        if self.opaque: output += 2 ** 6
        if self.blocking: output += 2 ** 7
        self.binarymaskarray = output


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
