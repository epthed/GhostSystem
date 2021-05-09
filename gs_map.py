import numpy as np
import json
from json import JSONEncoder
from bitarray import bitarray, util

from materials import materials, material_id
import globalvar


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
                 floor=0, binaryarray=0):
        # define only West North and Floor. Put the rest of the 3d grid together and all 6 sides are covered.
        # split them into a binary representation, bit 1 is WestBlocking, bit 2 is WestTransparent etc. then store the
        # resulting number in a numpy array for fastness in FoV/pathing calculations
        if (fill, west, north, floor) is not (0, 0, 0, 0):
            slabs = [fill, west, north, floor]
            for i, slab in enumerate(slabs):
                if type(slab) == str:
                    slabs[i] = material_id(slab)
            fill, west, north, floor = slabs
            self.fill = util.int2ba(fill, 7)
            self.west = util.int2ba(west, 7)
            self.north = util.int2ba(north, 7)
            self.floor = util.int2ba(floor, 7)

        if binaryarray != 0:  # if we're creating object from a passed in full tile int
            self.binaryarray = util.int2ba(binaryarray, 32)
            self.load_binaryarray()
        else:
            self.binaryarray = util.int2ba(binaryarray, 32)
            self.calc_binaryarray()

    def get_int(self):
        return util.ba2int(self.binaryarray)

    def load_binaryarray(self):
        self.fill = self.binaryarray[0:7]
        self.west = self.binaryarray[7:14]
        self.north = self.binaryarray[14:21]
        self.floor = self.binaryarray[21:28]

    def calc_binaryarray(self):
        self.binaryarray[0:7] = self.fill
        self.binaryarray[7:14] = self.west
        self.binaryarray[14:21] = self.north
        self.binaryarray[21:28] = self.floor

    def walkable(self):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return not fill['blocking'], not west['blocking'], not north['blocking'], not floor['blocking']

    def transparent(self):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return not fill['opaque'], not west['opaque'], not north['opaque'], not floor['opaque']


# save and load an individual tile
#        temp = json.dumps(self._objectarray[0][1][1], cls=MyEncoder, indent=4)
#        temp = json.loads(temp)
#        temp = Tile(**temp)
# load a full 3d chunk:
#        temp = json.loads(temp)
#        temp = [[[Tile(**x) for x in y] for y in z] for z in temp]

class MapManager:
    def __init__(self):
        self.districts_grid = np.arange(100).reshape(10, -1)  # 20 megs when exported
        self.districts = []  # main memory object of all the districts
        for district in range(100):
            self.districts.append(None)


class Map:
    def __init__(self, y=100, x=100, z=30):
        # address by z,y,x 0,0,0 is bottom height, west, and north
        # https://stackoverflow.com/a/15311166

        self.nparray = np.zeros((z, y, x), dtype=np.uint32)
        self.nparray[0] = self.nparray[0] + 48  # 48 is concrete/3 floor with nothing else. setting

    def _testmap(self):
        # for idz, zSlice in enumerate(self._objectarray):  # z iteration, outside in
        #     for idy, ySlice in enumerate(zSlice):
        #         for idx, cell in enumerate(ySlice):
        #             if idx % 2 == 0 and idy % 2 == 0:
        #                 cell.fluid = "test"
        #                 if self._objectarray[idz][idy][idx] == cell:
        #                     pass
        example_tile = Tile(floor='concrete', fill='smoke')
        debug_floor_number = example_tile.get_int()
        walkable = example_tile.walkable()
        seethrough = Tile(binaryarray=48).transparent()
        for district in range(100):
            self.districts[district] = get_district(district)
        insert = np.zeros((2, 5, 5), dtype=np.uint32)
        insert = np.add(insert, 55)
        self.insert(insert, self.nparray, l=(0, 5, 5))

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


def get_district(district):
    globalvar.cursor.execute("SELECT map FROM mapdata WHERE id=%s", (district,))
    try:
        map_data = globalvar.cursor.fetchone()[0]
        map_data = np.array(map_data)
    except TypeError:
        map_data = np.zeros((30, 100, 100), dtype=np.uint32)
        insert_object = json.dumps(map_data.tolist())
        globalvar.cursor.execute("INSERT INTO mapdata (id, map) VALUES (%s, %s)", (district, insert_object))
        globalvar.conn.commit()
    return map_data


def save_district(map_data, district):
    insert_object = json.dumps(map_data.tolist())
    globalvar.cursor.execute("INSERT INTO mapdata (id, map) VALUES (%s, %s)", (district, insert_object))
    globalvar.conn.commit()


def insert(new_array, insertion_target, loc=(0, 0, 0), ):
    # new 3d array, insertion location at z,y,x, array to be inserted into
    # todo this works, add bounds checking and throw error if oob
    zidx = len(new_array)
    yidx = len(new_array[0])
    xidx = len(new_array[0][0])
    insertion_target[loc[0]:loc[0] + zidx, loc[1]:loc[1] + yidx, loc[2]:loc[2] + xidx] = new_array[:, :, :]
