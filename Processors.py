import esper
from numba import njit
# import socketio as sio
# import websocket
import asyncio
from skgeom import Polygon
import numpy as np

import Components as c
import gs_map


# only implement processors for stuff that runs or needs to check every turn.
# regular functions are just fine for one-offs in your Game class
# great opportunity for multithreading here, launch off many copies of heavy operations like FoV and pathing.

class MovementProcessor(esper.Processor):

    # @njit('void(void)')
    def process(self):
        pass
        # for ent, (vel, pos) in self.world.get_components(c.Velocity, c.Position):
        # todo add set updateFoV after something moves

        #     # pos.x += vel.x
        #     # pos.y += vel.y
        #     pos.x, pos.y = _jitmovementprocessor(vel.x, vel.y, pos.x, pos.y)
        #     # print('movement', {'ent': ent, "x": pos.x, "y": pos.y})
        #     # message = 'movement', {'ent': ent, "x": pos.x, "y": pos.y}
        #     # if self.world.has_component(ent, c.Renderable):
        #     #     print(ent, "is renderable")
        #     # else:
        #     #     print(ent, "is not renderable")
        #     # asyncio.create_task(sio.emit('movement', {'ent': ent, "x": pos.x, "y": pos.y}))
        #     # asyncio create_task basically fires this off immediately.TODO sum up all the changes and broadcast at once
        #
        #     # sio.my_event(sio.sid, message)


@njit()  # can use numba if you only pass in basic types. Passing in Component, not ok. Passing in specific values = ok
def _jitmovementprocessor(velx, vely, posx, posy):
    posx += velx
    posy += vely
    return posx, posy


class DistrictProcessor(esper.Processor):
    def process(self):
        (_, districts) = self.world.get_component(c.ActiveDistricts)[0]
        # districts = self.world.get_component(c.ActiveDistricts)
        current_districts = list(set(districts.active_districts))
        # print(current_districts)
        # districts.active_districts
        for ent, (character, position) in self.world.get_components(c.Character, c.Position):
            districts.active_districts.append(position.district)
        districts.active_districts = list(set(districts.active_districts))
        if (districts.active_districts != current_districts) and (len(districts.active_districts) > 0):
            self.world.add_component(_, c.UpdateMap())  # todo right now it updates all of them


class MapProcessor(esper.Processor):
    def process(self):
        for ent, (position) in self.world.get_component(c.UpdateMap):
            print("updating map")
            # only continue processing if the mapupdate component-tag is present
            # todo trigger update on map changing as well as players moving around
            self.world.remove_component(ent, c.UpdateMap)
            # ^^^ remove it and continue processing. Always remove non-() components
            (_, mapManager) = self.world.get_component(gs_map.MapManager)[0]
            (_, districts) = self.world.get_component(c.ActiveDistricts)[0]
            (_, maps) = self.world.get_component(c.DistrictMaps)[0]
            # for _, (map_object) in self.world.get_component(gs_map.Map):
            #     self.world.delete_entity(_, immediate=True)  # todo redo deletion

            mapManager.update_districts(districts.active_districts)
            # for district in districts.active_districts:
            #     self.world.create_entity(gs_map.Map(mapManager.districts_active_maps[district], district=district))
            for district in districts.active_districts:
                maps.mapList[district] = gs_map.Map(mapManager.districts_active_maps[district], district=district)


class FovProcessor(esper.Processor):
    def __init__(self, sio):
        self.sio = sio

    def process(self):
        updated_fovs = []
        for ent, (_) in self.world.get_component(c.UpdateFov):
            person = self.world.component_for_entity(ent, c.Person)
            position = self.world.component_for_entity(ent, c.Position)
            (_, maps) = self.world.get_component(c.DistrictMaps)[0]
            if maps.mapList[position.district] is None:
                updated_fovs.append(ent)
                continue
            person.fov = maps.mapList[position.district].calc_fov(position.z, position.y, position.x)
            # person.fov[0] = array of boolean grid visibility, [1] is horizontal walls, [2] is vertical walls
            if self.world.has_component(ent, c.Character):
                character = self.world.component_for_entity(ent, c.Character)
                # todo get render information here

                asyncio.create_task(self.sio.emit('map_update', to=character.sid, data="you did it ayyy"))
                # todo send and catch the info
            updated_fovs.append(ent)
        for _ in updated_fovs:
            self.world.remove_component(_, c.UpdateFov)

            pass
