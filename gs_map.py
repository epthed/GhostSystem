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
                 floor=0, binaryarray=None):
        # define only West North and Floor. Put the rest of the 3d grid together and all 6 sides are covered.
        # split them into a binary representation, bit 1 is WestBlocking, bit 2 is WestTransparent etc. then store the
        # resulting number in a numpy array for fastness in FoV/pathing calculations
        if (fill, west, north, floor) != (0, 0, 0, 0):
            slabs = [fill, west, north, floor]
            for i, slab in enumerate(slabs):
                if type(slab) == str:
                    slabs[i] = material_id(slab)
            fill, west, north, floor = slabs
            self.fill = util.int2ba(fill, 7)
            self.west = util.int2ba(west, 7)
            self.north = util.int2ba(north, 7)
            self.floor = util.int2ba(floor, 7)

        if binaryarray is not None:  # if we're creating object from a passed in full tile int
            self.binaryarray = util.int2ba(int(binaryarray), 32)
            self.load_binaryarray()
        else:
            self.binaryarray = util.int2ba(0, 32)
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
        # for district in range(100):
        #     self.districts[district] = get_district(district)
        insert_array = np.zeros((2, 5, 5), dtype=np.uint32)
        insert_array = np.add(insert_array, 55)
        test_insertion_target = np.zeros((30, 100, 100), dtype=np.uint32)
        test_insertion_target = insert(insert_array, test_insertion_target, loc=(0, 5, 5))
        pass


class Map:
    def __init__(self, y=100, x=100, z=30):
        # address by z,y,x 0,0,0 is bottom height, west, and north
        # https://stackoverflow.com/a/15311166

        self.nparray = np.zeros((30, 100, 100), dtype=np.uint32)
        self.nparray[0] = self.nparray[0] + 48  # 48 is concrete/3 floor with nothing else. setting
        insert_array = np.zeros((1, 5, 5), dtype=np.uint32)
        insert_array = np.add(insert_array, 67108912)
        self.nparray = insert(insert_array, self.nparray, loc=(0, 3, 3))

        self.fov = True  # use setter to force recalculation

    @property
    def transparent(self) -> np.ndarray:
        return self.transparent

    @property
    def walkable(self) -> np.ndarray:
        return self.walkable

    @property
    def fov(self) -> np.ndarray:
        return self.fov

    @fov.setter
    def fov(self, value):
        unique_tiles = np.unique(self.nparray)
        visibility_angles = []
        for source in unique_tiles:
            for destination in unique_tiles:
                source_transparency = Tile(binaryarray=source).transparent()
                destination_transparency = Tile(binaryarray=destination).transparent()
                if not source_transparency[0] or not destination_transparency[0]:  # if the source or dest is filled
                    # with opaque materials then set all direction checks to false
                    visibility_angles.append([False, False, False, False, False, False, False, False])
                    continue
                pass

        # try constructing 2d numpy boolean list of valid visible tile/walls
        # 1 2 3
        # 4 s 5    "s" is source tile
        # 6 7 8
        # combinatorial: example 0-0, 0-48, 48-0, 48-48 scales with uniques^2
        # return not fill['opaque'], not west['opaque'], not north['opaque'], not floor['opaque']

    #
    # @transparent.setter
    # def transparent(self, recalculate):
    #
    #     pass


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
    return insertion_target
