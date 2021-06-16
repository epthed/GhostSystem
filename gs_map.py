import numpy as np
import json
from json import JSONEncoder
from bitarray import bitarray, util
from typing import Union, Tuple
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL.CGAL_AABB_tree import AABB_tree_Polyhedron_3_Facet_handle
from CGAL.CGAL_Kernel import Point_3, centroid, Segment_3
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
        self.districts_in_use = [0] * 100  # counter of districts in use for active actors
        self.districts_active_maps = [None] * 100

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
        self.districts_in_use = [0] * 100  # reset memory counter
        size = 1  # guarantee at least this * 100m visibility. 1: 300x300, 2: 500x500, 3:700x700
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
                    self.districts_in_use[district] += 1  # remember that this district is in use
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
            if usage == 0 and self.districts[district] is not None:
                save_district(self.districts[district], district)
                self.districts[district] = None


class Map:
    # each active district has one of these, contains their FoV and navmap. NPCs and players in the same
    # spot calculate their FoV and nav as a sub of this playerMap
    def __init__(self, _nparray: np.array, district: int):  #
        # address by z,y,x 0,0,0 is bottom height, west, and north
        # https://stackoverflow.com/a/15311166
        # print("initializing a map for", district)
        self.map = _nparray
        self.district = district
        # self.initialize_skgeom()
        # self.fov = True  # use setter to force recalculation
        self.fov = None

    def calc_fov_map(self, z_in: int = 0, y_in: int = 0, x_in: int = 0):
        if self.fov is None:
            self.fov = FieldOfView(self.map)
        # else:
        #     fov_object.update_map(self.map) # todo smart incrementalism
        visible = self.fov.calc_fov(z_in, y_in, x_in)
        return visible
        wall_horizontal = []
        wall_vertical = []

        for z in z_levels:
            vs = self.z_levels[z]
            q = Point2(y_in + .5, x_in + .5)
            face = outer_box.find(q)
            vx = vs.compute_visibility(q, face)

            visible_polygon = Polygon([item.point() for item in vx.vertices])
            bbox = visible_polygon.bbox()

            for edge in visible_polygon.edges:
                if edge.is_vertical():  # ***is_horizontal*** and is_vertical are swapped because of y,x convention
                    y = int(edge.source().x().__float__())
                    if y == 0 or y == max_y: continue
                    x_start = edge.source().y().__float__()  # iterate upward from lower x until >= x_dest
                    x_dest = edge.target().y().__float__()
                    if x_dest < x_start:
                        x_start, x_dest = x_dest, x_start
                    for x in range(int(x_start), int(x_dest + .9)):  # add .9 and re-floor to show partial-visible walls
                        wall_horizontal.append([y, x, self.map[z, y, x]])
                if edge.is_horizontal():  # ***is_vertical***
                    x = int(edge.source().y().__float__())
                    if x == 0 or x == max_x: continue
                    y_start = edge.source().x().__float__()  # iterate upward from lower y
                    y_dest = edge.target().x().__float__()
                    if y_dest < y_start:
                        y_start, y_dest = y_dest, y_start
                    for y in range(int(y_start), int(y_dest + .9)):  # add .9 and re-floor to show partial-visible walls
                        wall_vertical.append([y, x, self.map[z, y, x]])
            # todo loop through all y,x in bounding box and get map info if oriented_side(y.5,x.5) is positive
            if sum(1 for item in iter(vx.vertices)) == 4:  # if the z level is empty
                if not need_3d:
                    visible_map[:] = True
                else:
                    visible_map[z] = True
            else:
                for y in range(int(bbox.xmin()), int(bbox.xmax())):
                    for x in range(int(bbox.ymin()), int(bbox.ymax())):
                        q = Point2(y + .5, x + .5)
                        sign = visible_polygon.oriented_side(q)
                        if sign == 1 or sign == 0:  # 1 is inside, 0 is on the edge, -1 is outside.
                            # include edge visibility as a design choice
                            if not need_3d:
                                visible_map[0, y, x] = True
                            else:
                                visible_map[z, y, x] = True

        pass
        return fov_object


class FieldOfView:  # One of these per district. Persons ask this class what they can see
    # todo add initialization with geometry
    # todo add function to return visible entities
    def __init__(self, _nparray: np.array):
        self.polygon = Polyhedron_3()
        unique_visibilities = List()
        unique_visibilities_index = List()
        unique_visibilities_id = List()
        for unique_integer in np.unique(_nparray):
            unique_visibilities.append(Tile(binaryarray=unique_integer).opaque())
            unique_visibilities_id.append(Tile(binaryarray=unique_integer).opaque_id())
            unique_visibilities_index.append(unique_integer)

        horizontal, vertical, flat = visibility_geometry_from_nparray(unique_visibilities, unique_visibilities_id,
                                                                      unique_visibilities_index, _nparray)
        self.potential_visible_slabs = []
        horizontals = np.nonzero(horizontal)
        verticals = np.nonzero(vertical)
        flats = np.nonzero(flat)
        for i in range(horizontals[0].shape[0]):
            z = int(horizontals[0][i])
            y = int(horizontals[1][i])
            x = int(horizontals[2][i])
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y, x),
                                                                  Point_3(z, y, x + 1),
                                                                  Point_3(z + 1, y, x + 1),
                                                                  Point_3(z + 1, y, x), ),
                                                 horizontal[z, y, x], 2))  # north
        for i in range(verticals[0].shape[0]):
            z = int(verticals[0][i])
            y = int(verticals[1][i])
            x = int(verticals[2][i])
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y + 1, x),
                                                                  Point_3(z, y, x),
                                                                  Point_3(z + 1, y, x),
                                                                  Point_3(z + 1, y + 1, x), ),
                                                 vertical[z, y, x], 1))  # west
        for i in range(flats[0].shape[0]):
            z = int(flats[0][i])
            y = int(flats[1][i])
            x = int(flats[2][i])
            self.potential_visible_slabs.append((z, y, x,
                                                 self.create_quad(Point_3(z, y + 1, x),
                                                                  Point_3(z, y + 1, x + 1),
                                                                  Point_3(z, y, x + 1),
                                                                  Point_3(z, y, x), ),
                                                 flat[z, y, x], 0))  # floor
        self.aabb = AABB_tree_Polyhedron_3_Facet_handle(self.polygon.facets())

    def create_quad(self, a: Point_3, b: Point_3, c: Point_3, d: Point_3):  # must be inserted in ccw order
        h = self.polygon.make_triangle(a, b, c)
        g = self.polygon.split_edge(h)
        g.vertex().set_point(d)
        return centroid(a, b, c, d)

    def update_map(self, _nparray: np.array):  # todo make this a smarter incremental and not nuke-n-pave
        self.__init__(_nparray)

    def calc_fov(self, z_in: int = 0, y_in: int = 0, x_in: int = 0):
        viewpoint = Point_3(z_in + .5, y_in + .5, x_in + .5)
        visible_slabs = []
        for z, y, x, center, slab_id, location in self.potential_visible_slabs:
            test_segment = Segment_3(viewpoint, center)
            if self.aabb.number_of_intersected_primitives(test_segment) < 2:  # intersect any slabs besides itself?
                visible_slabs.append((z, y, x, slab_id, location))
        return visible_slabs
        pass


def arrangement_from_3d(_map: np.array):
    # y,x 0,0 is top left
    max_x = _map.shape[2]
    max_y = _map.shape[1]
    max_z = _map.shape[0]
    unique_visibilities = List()
    unique_visibilities_index = List()
    unique_visibilities_id = List()
    for unique_integer in np.unique(_map):
        unique_visibilities.append(Tile(binaryarray=unique_integer).opaque())
        unique_visibilities_id.append(Tile(binaryarray=unique_integer).opaque_id())
        unique_visibilities_index.append(unique_integer)
        # locations[unique_integer] = np.nonzero(z_map == unique_integer)
    exit_filled, exit_empty = 0, 0
    for [fill, west, north, _] in unique_visibilities:  # early exit if all empty or full
        if not (fill or west or north):
            exit_empty += 1
        if fill:
            exit_filled += 1
    if exit_empty == len(unique_visibilities_index):
        vs = TriangularExpansionVisibility(outer_box)
        return vs
    # for key, item in locals().items():
    #     print(key, type(item))
    # print("initial")
    # West  y`=y   x'=x-1
    # North y`=y-1 x'=x
    # South y'=y+1 x'=x
    # East  y'=y   x'=x+1

    horizontal, vertical = visibility_geometry_from_nparray(unique_visibilities, unique_visibilities_index, z_map)
    arr = arrangement.Arrangement()
    for s in outer:
        arr.insert(s)
    # try to scan down each row for continual lines
    for y in range(horizontal.shape[0]):
        start = None
        for x in range(horizontal.shape[1]):
            if horizontal[y, x]:
                # if we're to draw a line here
                if start is None:
                    start = Point2(y, x)
                continue
            if start is not None:
                finish = Point2(y, x)
                arr.insert(Segment2(start, finish))
                start = None
    # try to scan down each column for continual lines
    for x in range(vertical.shape[1]):
        start = None
        for y in range(vertical.shape[0]):
            if vertical[y, x]:
                # if we're to draw a line here
                if start is None:
                    start = Point2(y, x)
                continue
            if start is not None:
                finish = Point2(y, x)
                arr.insert(Segment2(start, finish))
                start = None
    # for s in segments:
    #     s = Segment2(Point2(s[0], s[1]), Point2(s[2], s[3]))
    #     arr.insert(s)
    vs = TriangularExpansionVisibility(arr)  # calc and store the precomputed triangular expansion information
    # from here until return is debug
    # for key, item in locals().items():
    #     print(key, type(item))
    # print("finale")
    # exit(0)
    # q = Point2(.5, .75)
    # face = outer_box.find(q)
    # vx = vs.compute_visibility(q, face)
    # print(sum(1 for item in iter(arr.vertices)), sum(1 for item in iter(arr.faces)),
    #       sum(1 for item in iter(arr.halfedges)))
    # print(sum(1 for item in iter(vx.vertices)), sum(1 for item in iter(vx.faces)),
    #       sum(1 for item in iter(vx.halfedges)))
    # draw.plt.xlim([0, 10])
    # draw.plt.ylim([0, 10])
    # draw.plt.gcf().set_dpi(300)
    # for he in arr.halfedges:
    #     draw.draw(he.curve(), visible_point=True)
    # for v in vx.halfedges:
    #     draw.draw(v.curve(), color='red', visible_point=False)
    # draw.draw(q, color='magenta')
    # fig = draw.plt.figure()
    # fig.set_ylim(0, 10)

    # fig.set_xlim(0, 10)
    # draw.plt.show()
    # x=12
    # pass
    return vs


# todo extend to 3d and feed the visibility class
@njit(parallel=True)
def visibility_geometry_from_nparray(unique_visibilities: List, unique_visibilities_id: List,
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
                fill, west, north, floor = unique_visibilities[tile_index]
                if fill:
                    # any fills are overridden by explicit slabs
                    if vertical[z, y, x] is np.int8(0): vertical[z, y, x] = slab_id_fill  # west
                    if x != _map.shape[2] - 1:
                        if vertical[z, y, x + 1] is np.int8(0): vertical[z, y, x + 1] = slab_id_fill  # east
                    if horizontal[z, y, x] is np.int8(0): horizontal[z, y, x] = slab_id_fill  # north
                    if y != _map.shape[1] - 1:
                        if horizontal[z, y + 1, x] is np.int8(0): horizontal[z, y + 1, x] = slab_id_fill  # south
                    if flat[z, y, x] is np.int8(0): flat[z, y, x] = slab_id_fill  # floor
                    if z != _map.shape[0] - 1:
                        if flat[z + 1, y, x] is np.int8(0): flat[z + 1, y, x] = slab_id_fill  # ceiling

                if west and x != 0:
                    vertical[z, y, x] = slab_id_west  # west
                if north and y != 0:
                    horizontal[z, y, x] = slab_id_north  # north
                if floor:
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
        map_data = np.zeros((30, 100, 100), dtype=np.uint32)
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
