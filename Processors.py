import esper
from numba import njit
# import socketio
# import websocket
import asyncio

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

            for _, (map_object) in self.world.get_component(gs_map.Map):
                self.world.delete_entity(_, immediate=True)  # todo right now it deletes all of them

            mapManager.update_districts(districts.active_districts)
            for district in districts.active_districts:
                self.world.create_entity(gs_map.Map(mapManager.districts_active_maps[district], district=district))
