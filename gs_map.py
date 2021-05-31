import numpy as np
import json
from json import JSONEncoder
from bitarray import bitarray, util
from typing import Union

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

    # make tile/slab just helper functions of getting info from or into a number. Tile(number).east.blocking => bool


class Tile:

    def __init__(self, fill: Union[int, str] = 0, west: Union[int, str] = 0, north: Union[int, str] = 0,
                 floor: Union[int, str] = 0, binaryarray: int = None):
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

    def get_int(self) -> int:
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

    def walkable(self) -> (bool, bool, bool, bool):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return not fill['blocking'], not west['blocking'], not north['blocking'], not floor['blocking']

    def transparent(self) -> (bool, bool, bool, bool):
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

    # todo expand for multiple sets of actors. Right now only handles a single actor

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

    def update_districts(self, actors_in_districts: dict):
        # function returns a 3x3 district grid numpy 3d array for each player actor,
        # shared if they are in the same district.
        districts_with_actors = {}
        for key, value in actors_in_districts.items():
            districts_with_actors.setdefault(value, []).append(key)  # invert mapping
        for loc_actor in districts_with_actors.items():
            loc = loc_actor[0]
            actor = loc_actor[1]
            district_index = np.nonzero(self.districts_grid == loc)  # returns y,x pair
            get_y = [district_index[0][0]]
            get_x = [district_index[1][0]]
            if district_index[0] != 0:
                get_y.append(district_index[0][0] - 1)
            if district_index[0] != self.districts_grid.shape[0]:
                get_y.append(district_index[0][0] + 1)
            if district_index[1] != 0:
                get_x.append(district_index[1][0] - 1)
            if district_index[1] != self.districts_grid.shape[1]:
                get_x.append(district_index[1][0] + 1)
            for y in get_y:
                for x in get_x:
                    district = self.districts_grid[y][x]
                    if self.districts[district] is None:
                        self.districts[district] = get_district(int(district))


class Map:
    # each player in a unique district has one of these, contains their FoV and navmap. NPCs and players in the same
    # spot calculate their FoV and nav as a sub of this playerMap
    def __init__(self, y=100, x=100, z=30):  # todo pass in the already complete 3d nparray
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
                local_valid_paths = []
                source_transparency = Tile(binaryarray=source).transparent()
                destination_transparency = Tile(binaryarray=destination).transparent()
                if not source_transparency[0] or not destination_transparency[0]:  # if the source or dest is filled
                    # with opaque materials then set all direction checks to false
                    visibility_angles.append([False, False, False, False, False, False, False, False])
                    continue
                # each of the directions in order
                local_valid_paths.append((source_transparency[1] and source_transparency[2]))  # 0 north or west
                local_valid_paths.append(source_transparency[2])  # 1 north
                local_valid_paths.append((destination_transparency[1] and source_transparency[2]))  # 2 north or east

                visibility_angles.append(local_valid_paths)
                pass

        # try constructing 2d numpy boolean list of valid visible tile/walls
        # 0 1 2
        # 3 s 4    "s" is source tile
        # 5 6 7
        # combinatorial: example 0-0, 0-48, 48-0, 48-48 scales with uniques^2
        # return not fill['opaque'], not west['opaque'], not north['opaque'], not floor['opaque']

    #
    # @transparent.setter
    # def transparent(self, recalculate):
    #
    #     pass


def get_district(district: int):
    try:
        globalvar.cursor.execute("SELECT map FROM mapdata WHERE id=%s", (district,))
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
