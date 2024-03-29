import numpy as np
import json
from json import JSONEncoder
from bitarray import bitarray, util
from typing import Union, Tuple
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL.CGAL_AABB_tree import AABB_tree_Polyhedron_3_Facet_handle
from CGAL.CGAL_Kernel import Point_3, centroid, Segment_3, Vector_3
from numba import njit, int8
from numba.experimental import jitclass
from numba.typed import List, Dict

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

    def blocking(self) -> (bool, bool, bool, bool):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return fill['blocking'], west['blocking'], north['blocking'], floor['blocking']

    def opaque(self) -> (bool, bool, bool, bool):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return fill['opaque'], west['opaque'], north['opaque'], floor['opaque']

    def opaque_id(self) -> (int, int, int, int):
        fill = materials(util.ba2int(self.fill))
        west = materials(util.ba2int(self.west))
        north = materials(util.ba2int(self.north))
        floor = materials(util.ba2int(self.floor))
        return fill['number'], west['number'], north['number'], floor['number']


# save and load an individual tile
#        temp = json.dumps(self._objectarray[0][1][1], cls=MyEncoder, indent=4)
#        temp = json.loads(temp)
#        temp = Tile(**temp)
# load a full 3d chunk:
#        temp = json.loads(temp)
#        temp = [[[Tile(**x) for x in y] for y in z] for z in temp]

class MapManager:
    def __init__(self):
        self.districts_grid = np.arange(100).reshape(10, -1)  # 20 megs when exported, 100x100 would fill up the prod
        # DB on it's own. also each district is 1.2mb in memory. the server has 512mb total.
        self.districts: Union[None, np.array] = [None] * 100  # main memory object of all the districts
        self.districts_in_use = [list()] * 100  # counter of districts in use for active actors
        self.districts_active_maps = [None] * 100
        self.feed_district_offsets = [list()] * 100  # districts that feed an active district, with offset info

    def _testmap(self):  # debug/learning function
        # for idz, zSlice in enumerate(self._objectarray):  # z iteration, outside in
        #     for idy, ySlice in enumerate(zSlice):
        #         for idx, cell in enumerate(ySlice):
        #             if idx % 2 == 0 and idy % 2 == 0:
        #                 cell.fluid = "test"
        #                 if self._objectarray[idz][idy][idx] == cell:
        #                     pass
        conc_floor = Tile(floor='concrete').get_int()
        conc_west = Tile(west='concrete', floor='concrete').get_int()
        conc_north = Tile(north='concrete', floor='concrete').get_int()
        conc_northwest = Tile(west='concrete', north='concrete', floor='concrete').get_int()
        # walkable = example_tile.walkable()
        seethrough = Tile(binaryarray=48).opaque()
        # for district in range(100):
        #     self.districts[district] = get_district(district)
        insert_array = np.zeros((2, 5, 5), dtype=np.uint32)
        insert_array = np.add(insert_array, 55)
        test_insertion_target = np.zeros((30, 100, 100), dtype=np.uint32)
        test_insertion_target = insert(insert_array, test_insertion_target, loc=(0, 5, 5))

        self.nparray = np.zeros((30, 100, 100), dtype=np.uint32)
        self.nparray[0] = self.nparray[0] + 48  # 48 is concrete/3 floor with nothing else. setting
        insert_array = np.zeros((1, 5, 5), dtype=np.uint32)
        insert_array = np.add(insert_array, 67108912)
        self.nparray = insert(insert_array, self.nparray, loc=(0, 3, 3))

        pass

    def load_district_from_yx(self, y: int, x: int):
        district = self.districts_grid[y][x]
        return self.districts[district]

    def update_districts(self, active_districts: List[int]):
        # function returns a district grid numpy 3d array for each player actor,
        # shared if they are in the same district.
        self.districts_in_use = [list()] * 100  # reset memory counter
        size = 1  # guarantee at least this * 100m visibility. 0: 100x100 1: 300x300, 2: 500x500, 3:700x700
        # changed district width to 30m. 0: 30x30 1:90x90, 2:150x150, 3:240x240
        MAP_WIDTH = 30
        finalized_maps = []
        for loc in active_districts:
            district_index = np.nonzero(self.districts_grid == loc)  # returns y,x pair
            get_y = [district_index[0][0]]
            get_x = [district_index[1][0]]
            max_y = self.districts_grid.shape[0] - 1  # last valid y index
            max_x = self.districts_grid.shape[1] - 1
            for i in range(1, size + 1):
                if get_y[0] - i >= 0:
                    # y north of core
                    get_y.append(get_y[0] - i)
                if get_y[0] + i <= max_y:
                    # y south of core
                    get_y.append(get_y[0] + i)
                if get_x[0] - i >= 0:
                    # x west of core
                    get_x.append(get_x[0] - i)
                if get_x[0] + i <= max_x:
                    # x east of core
                    get_x.append(get_x[0] + i)
            for y in get_y:
                for x in get_x:
                    district: int = self.districts_grid[y][x]
                    temp_list = self.districts_in_use[district].copy()
                    temp_list.append(loc)
                    self.districts_in_use[district] = temp_list

                    original_y = district_index[0][0]
                    original_x = district_index[1][0]
                    temp_list = self.feed_district_offsets[loc].copy()
                    temp_list.append((district, MAP_WIDTH * (y - min(get_y)), MAP_WIDTH * (x - min(get_x))))
                    self.feed_district_offsets[loc] = temp_list
                    # remember that this district is in use
                    if self.districts[district] is None:
                        self.districts[district] = get_district(int(district))
                        # we now know all the districts we want are loaded.
            y_rows = []
            for y in sorted(get_y):
                districts = []
                for x in sorted(get_x):
                    districts.append(self.load_district_from_yx(y, x))

                    # districts.append(np.zeros((2, 2, 2))+y+x)  # test correct shape
                y_rows.append(np.concatenate(districts, axis=2))
            map_for_location = np.concatenate(y_rows, axis=1)
            self.districts_active_maps[loc] = map_for_location
        for district, usage in enumerate(self.districts_in_use):
            if usage == [] and self.districts[district] is not None:
                save_district(self.districts[district], district)
                self.districts[district] = None
        return self.districts_in_use, self.feed_district_offsets


class Map:
    # each active district has one of these, contains their FoV and navmap. NPCs and players in the same
    # spot calculate their FoV and nav as a sub of this playerMap. Also store list of entities and locations
    # todo pass in district information so I can do relative positioning
    def __init__(self, _nparray: np.array, district: int, entities: list, offsets: list):  #
        # address by z,y,x 0,0,0 is bottom height, west, and north
        # https://stackoverflow.com/a/15311166
        # print("initializing a map for", district)
        self.map = _nparray
        self.district = district
        self.fov = None
        self.offsets = offsets
        self.entities = []
        for entity in entities:
            self.entities.append((entity[0], *self.apply_offsets(entity[1], entity[2], entity[3], entity[4])))

    def apply_offsets(self, z, y, x, district):
        for offset in self.offsets:
            if offset[0] == district:
                y += offset[1]
                x += offset[2]
        return z, int(y), int(x)

    def calc_fov_map(self, z_in: int = 0, y_in: int = 0, x_in: int = 0, district_in: int = 0):
        if self.fov is None:
            self.fov = FieldOfView(self.map)
        # else:
        #     fov_object.update_map(self.map) # todo smart incrementalism
        visible_slabs = self.fov.calc_slab_fov(*self.apply_offsets(z_in, y_in, x_in, district_in))
        return visible_slabs

    def calc_fov_ents(self, ent: int):
        if self.fov is None:
            self.fov = FieldOfView(self.map)
        # else:
        #     fov_object.update_map(self.map) # todo smart incrementalism
        visible_ents = self.fov.calc_ent_fov(self.entities, ent)
        return visible_ents


class FieldOfView:  # One of these per district. Persons ask this class what they can see
    # todo add function to return visible entities

    # @njit()
    def __init__(self, _nparray: np.array):
        self.polygon = Polyhedron_3()
        unique_visibilities = List()
        unique_visibilities_index = List()
        unique_visibilities_id = List()
        for unique_integer in np.unique(_nparray):
            unique_visibilities.append(Tile(binaryarray=unique_integer).opaque())
            unique_visibilities_id.append(Tile(binaryarray=unique_integer).opaque_id())
            unique_visibilities_index.append(unique_integer)

        horizontal, vertical, flat = visibility_geometry_from_nparray(unique_visibilities_id,
                                                                      unique_visibilities_index, _nparray)
        self.potential_visible_slabs = []
        horizontals = np.nonzero(horizontal)
        verticals = np.nonzero(vertical)
        flats = np.nonzero(flat)

        self.translucent_id = {1}  # slab material IDs that are to be shown, but don't block LoS.
        # gonna be a long list/set eventually. Not for space-filling item like a desk, that will be an entity.

        for i in range(horizontals[0].shape[0]):
            z = int(horizontals[0][i])
            y = int(horizontals[1][i])
            x = int(horizontals[2][i])
            create_geom = True
            if vertical[z, y, x] in self.translucent_id:
                create_geom = False
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y, x),
                                                                  Point_3(z, y, x + 1),
                                                                  Point_3(z + 1, y, x + 1),
                                                                  Point_3(z + 1, y, x), create_geom=create_geom),
                                                 horizontal[z, y, x], 2))  # north
        for i in range(verticals[0].shape[0]):
            z = int(verticals[0][i])
            y = int(verticals[1][i])
            x = int(verticals[2][i])
            create_geom = True
            if vertical[z, y, x] in self.translucent_id:
                create_geom = False
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y + 1, x),
                                                                  Point_3(z, y, x),
                                                                  Point_3(z + 1, y, x),
                                                                  Point_3(z + 1, y + 1, x), create_geom=create_geom),
                                                 vertical[z, y, x], 1))  # west
        for i in range(flats[0].shape[0]):
            z = int(flats[0][i])
            y = int(flats[1][i])
            x = int(flats[2][i])
            create_geom = True
            if z == 0 or flat[z, y, x] in self.translucent_id:
                create_geom = False
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y + 1, x),
                                                                  Point_3(z, y + 1, x + 1),
                                                                  Point_3(z, y, x + 1),
                                                                  Point_3(z, y, x), create_geom=create_geom),
                                                 flat[z, y, x], 0))  # floor

        self.aabb = AABB_tree_Polyhedron_3_Facet_handle(self.polygon.facets())

    def create_quad(self, a: Point_3, b: Point_3, c: Point_3, d: Point_3,
                    create_geom=True):  # must be inserted in ccw order
        if create_geom:
            h = self.polygon.make_triangle(a, b, c)
            g = self.polygon.split_edge(h)
            g.vertex().set_point(d)
        center = centroid(a, b, c, d)
        return center

    def update_map(self, _nparray: np.array):  # todo make this a smarter incremental and not nuke-n-pave
        self.__init__(_nparray)

    # @njit() can't njit the stuff using ANY cgal functions
    def calc_slab_fov(self, z_in: int = 0, y_in: int = 0, x_in: int = 0):
        viewpoint = Point_3(z_in + .5, y_in + .5, x_in + .5)
        # destination = Point_3(z_in + 1, y_in + 1, x_in + 1)
        visible_slabs = []
        # test_segment = Segment_3(viewpoint, destination)
        for z, y, x, center, slab_id, location in self.potential_visible_slabs:
            test_segment = Segment_3(viewpoint, center)
            if (z == 0 and location == 0) or slab_id in self.translucent_id:
                if not self.aabb.do_intersect(test_segment):  # check if intersect any slabs for the ground or glass
                    visible_slabs.append((z, y, x, int(slab_id), location))
            else:
                if self.aabb.number_of_intersected_primitives(test_segment) < 2:
                    # check if it intersects itself and another for all other cases
                    visible_slabs.append((z, y, x, int(slab_id), location))
        return visible_slabs
        pass

    def calc_ent_fov(self, entities: list, ent: int):

        visible_entities = []
        for entity_source in entities:
            if entity_source[0] != ent:
                continue
            viewpoint = Point_3(entity_source[1] + .5, entity_source[2] + .5, entity_source[3] + .5)
            for entity_target in entities:
                # 0 ent, 1 pos.z, 2 pos.y, 3 pos.x,
                center = Point_3(entity_target[1] + .5, entity_target[2] + .5, entity_target[3] + .5)
                test_segment = Segment_3(viewpoint, center)
                if not self.aabb.do_intersect(test_segment):  # check if intersect any slabs
                    visible_entities.append((entity_target))
        return visible_entities


@njit(parallel=True, cache=True)
def visibility_geometry_from_nparray(unique_visibilities_id: List,
                                     unique_visibilities_index: List, _map: np.array) -> (np.array, np.array, np.array):
    '''
    West  y=>y   x=>x-1
    North y=>y-1 x=>x
    South y=>y+1 x=>x
    East  y=>y   x=>x+1
    '''
    # geometries = np.array([[1, 2, 3, 4]], dtype=np.int64)
    horizontal = np.zeros(_map.shape, dtype=np.int8)  # declare horizonal wall array
    vertical = np.zeros(_map.shape, dtype=np.int8)  # declare vertical wall array
    flat = np.zeros(_map.shape, dtype=np.int8)  # declare floor/ceiling array
    # fill['opaque'], not west['opaque'], not north['opaque'],
    for z in range(_map.shape[0]):
        for y in range(_map.shape[1]):
            for x in range(_map.shape[2]):
                # visibility_info = Tile(binaryarray=map_integer).transparent()
                tile_int = _map[z, y, x]
                tile_index = unique_visibilities_index.index(tile_int)
                slab_id_fill, slab_id_west, slab_id_north, slab_id_floor, = unique_visibilities_id[tile_index]
                # fill, west, north, floor = unique_visibilities[tile_index]
                if slab_id_fill != 0:
                    # any fills are overridden by explicit slabs
                    if vertical[z, y, x] == 0:
                        vertical[z, y, x] = slab_id_fill  # west
                    if x != _map.shape[2] - 1:
                        if vertical[z, y, x + 1] == 0:
                            vertical[z, y, x + 1] = slab_id_fill  # east
                    if horizontal[z, y, x] == 0:
                        horizontal[z, y, x] = slab_id_fill  # north
                    if y != _map.shape[1] - 1:
                        if horizontal[z, y + 1, x] == 0:
                            horizontal[z, y + 1, x] = slab_id_fill  # south
                    if flat[z, y, x] == 0:
                        flat[z, y, x] = slab_id_fill  # floor
                    if z != _map.shape[0] - 1:
                        if flat[z + 1, y, x] == 0:
                            flat[z + 1, y, x] = slab_id_fill  # ceiling

                if slab_id_west != 0 and x != 0:
                    vertical[z, y, x] = slab_id_west  # west
                if slab_id_north != 0 and y != 0:
                    horizontal[z, y, x] = slab_id_north  # north
                if slab_id_floor != 0:
                    flat[z, y, x] = slab_id_floor  # floor
    # geometries = geometries[1:]
    pass
    return horizontal, vertical, flat


def get_district(district: int):
    try:
        globalvar.cursor.execute("SELECT map FROM mapdata WHERE id=%s", (district,))
        map_data = globalvar.cursor.fetchone()[0]
        map_data = np.array(map_data)
    except TypeError:
        globalvar.conn.rollback()
        map_data = np.zeros((30, 30, 30), dtype=np.uint32)
        map_data[0] = np.add(map_data[0], 48)
        conc_floor = Tile(floor='concrete').get_int()
        conc_west = Tile(west='concrete', floor='concrete').get_int()
        conc_north = Tile(north='concrete', floor='concrete').get_int()
        conc_northwest = Tile(west='concrete', north='concrete', floor='concrete').get_int()
        map_data[0][1:4, 1:4] = np.array([
            [conc_west, conc_northwest, conc_west],
            [conc_west, conc_floor, conc_west],
            [conc_north, conc_north, conc_floor]
        ])
        save_district(map_data, district)
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
