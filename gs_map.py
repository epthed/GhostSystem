import numpy as np
import json
from json import JSONEncoder

from materials import Materials

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class Slab:
    # this is the generic class for walls, floors, ceilings that are thin. Opaque true = can't see through
    def __init__(self, opaque=False, blocking=False, structure=0):
        self.opaque = opaque
        self.blocking = blocking
        self.structure = structure

    # todo: store everything in a 3d numpy array, fuck object arrays uint32 can store 32 true/false, uint64 etc
    # make tile/slab just helper functions of getting info from or into a number. tile.east.blocking(number) => bool


class Tile:
    def __init__(self, fill=0, west=0, north=0,
                 floor=0, binarymaskarray=0):
        # define only West North and Floor. Put the rest of the 3d grid together and all 6 sides are covered.
        # split them into a binary representation, bit 1 is WestBlocking, bit 2 is WestTransparent etc. then store the
        # resulting number in a numpy array for fastness in FoV/pathing calculations
        self.fill = fill  # these are only for if the entire 1m volume is opaque/blocking
        self.west = west
        self.north = north
        self.floor = floor
        self.binarymaskarray = binarymaskarray
        self.calc_binarymaskarray()

    def mask(self):
        return self.binarymaskarray

    def calc_binarymaskarray(self):
        output = 0
        if self.west.opaque: output += 2 ** 0
        if self.west.blocking: output += 2 ** 1
        if self.north.opaque: output += 2 ** 2
        if self.north.blocking: output += 2 ** 3
        if self.floor.opaque: output += 2 ** 4
        if self.floor.blocking: output += 2 ** 5
        if self.opaque: output += 2 ** 6
        if self.blocking: output += 2 ** 7
        self.binarymaskarray = output


# save and load an individual tile
#        temp = json.dumps(self._objectarray[0][1][1], cls=MyEncoder, indent=4)
#        temp = json.loads(temp)
#        temp = Tile(**temp)
# load a full 3d chunk:
#        temp = json.loads(temp)
#        temp = [[[Tile(**x) for x in y] for y in z] for z in temp]


class Map:
    def __init__(self, y=100, x=100, z=30, conn=None, cursor=None):
        # self._objectarray = [[[Tile() for _x in range(x)] for _y in range(y)] for _z in range(z)]
        #               x                                       y                       z
        # address by z,y,x 0,0,0 is bottom height, west, and north
        # https://stackoverflow.com/a/15311166
        # self._calculate_numpy()
        self.conn = conn
        self.cursor = cursor
        self.districts_grid = np.arange(100).reshape(10, -1)  # 20 megs when exported
        self.districts = []
        for district in range(100):
            self.districts.append(None)
        self.nparray = np.zeros((z, y, x), dtype=np.uint32)
        # self.nparray[0] = self.nparray[0] + 48 todo reinstate this creation of a global floor, the number changed

    def _testmap(self):
        # for idz, zSlice in enumerate(self._objectarray):  # z iteration, outside in
        #     for idy, ySlice in enumerate(zSlice):
        #         for idx, cell in enumerate(ySlice):
        #             if idx % 2 == 0 and idy % 2 == 0:
        #                 cell.fluid = "test"
        #                 if self._objectarray[idz][idy][idx] == cell:
        #                     pass
        mats = Materials()
        for district in range(100):
            self.districts[district] = self.get_district(district)
        insert = np.zeros((2, 5, 5), dtype=np.uint32)
        insert = np.add(insert, 55)
        self.insert(insert, l=(0, 5, 5))

    def get_district(self, district):
        self.cursor.execute("SELECT map FROM mapdata WHERE id=%s", (district,))
        try:
            map_data = self.cursor.fetchone()[0]
            map_data = np.array(map_data)
        except TypeError:
            map_data = np.zeros((30, 100, 100), dtype=np.uint32)
            insert_object = json.dumps(map_data.tolist())
            self.cursor.execute("INSERT INTO mapdata (id, map) VALUES (%s, %s)", (district, insert_object))
            self.conn.commit()
        return map_data

    def _calculate_numpy(self):
        self.nparray = np.array([[[x.mask() for x in y] for y in z] for z in self._objectarray],
                                subok=False, dtype=np.int32)
        # print(self._objectarray[0][1][1].north.__dict__)
        # print(self._objectarray[0][1][1].__dict__)
        # temp = json.dumps(self._objectarray[0][1][1].north, cls=MyEncoder)
        # temp = json.dumps(self._objectarray[0][1][1], cls=MyEncoder, indent=4)
        # temp = json.dumps(self._objectarray, cls=MyEncoder)
        # print(temp)
        # temp = json.loads(temp)
        # temp = [[[Tile(**x) for x in y] for y in z] for z in temp]
        # # temp = Tile(**temp)
        #
        # print(self.nparray[0][1][1])  # still addressed with z,y,x

    def insert(self, new_array, l=(0, 0, 0)):  # new 3d array, insertion location at z,y,x
        # todo this works, add bounds checking and throw error if oob
        zidx = len(new_array)
        yidx = len(new_array[0])
        xidx = len(new_array[0][0])
        self.nparray[l[0]:l[0] + zidx, l[1]:l[1] + yidx, l[2]:l[2] + xidx] = new_array[:, :, :]

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
