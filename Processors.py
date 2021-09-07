import esper
from numba import njit
# import socketio as sio
# import websocket
import asyncio
import numpy as np
import json

import Components as c
import gs_map
import globalvar


# only implement processors for stuff that runs or needs to check every turn.
# regular functions are just fine for one-offs in your Game class
# great opportunity for multithreading here, launch off many copies of heavy operations like FoV and pathing.

class MovementProcessor(esper.Processor):

    # @njit('void(void)')
    def process(self):
        pass
        for ent, (pos) in self.world.get_components(c.Position):
            # todo add set updateFoV after something moves
            pos = pos[0]
            desire_position = (pos.desire_z, pos.desire_y, pos.desire_x, pos.desire_district)
            if desire_position == (pos.z, pos.y, pos.x, pos.district):
                # don't wanna move, end movement processing.
                continue
            pass

            # todo add movement checking
            # todo add moving this entity to the requisite maps
            if pos.desire_district != pos.district:
                (_, districts) = self.world.get_component(c.ActiveDistricts)[0]
                # self.world.add_component(_, c.UpdateMap())
                self.world.add_component(ent, c.UpdateFov())

            # todo add new flag here to all currently visibile entities of this entity,
            #  that they need to update their entity fov: person.visible_entities
            # todo somehow register the entities that can see this one
            if pos.desire_district is None:
                pos.desire_z, pos.desire_y, pos.desire_x, pos.desire_district = pos.z, pos.y, pos.x, pos.district
            else:
                pos.z, pos.y, pos.x, pos.district = desire_position

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


class LoginProcessor(esper.Processor):
    def __init__(self, game, sio):
        self.sio = sio
        self.game = game

    # gets characters for people logged in

    def process(self):
        for ent, (connected_player) in self.world.get_component(c.ConnectedPlayer):
            if connected_player.character_entity == 0:
                try:
                    globalvar.cursor.execute("SELECT charname FROM characters WHERE username=%s",
                                             (connected_player.username,))
                    char_object = globalvar.cursor.fetchone()  # get existing character for this user.
                    if char_object is None: raise TypeError
                except TypeError:
                    globalvar.conn.rollback()
                if char_object is None: continue  # leave in a new character ready state
                character = self.game.load_character(char_object[0])
                if character:
                    connected_player.charName = char_object[0]
                    connected_player.character_entity = character
                    asyncio.create_task(self.sio.emit('existing_character', to=connected_player.sid,
                                                      data={'characterName': connected_player.charName,
                                                            'message': "Character " + connected_player.charName +
                                                                       " was loaded for user " + connected_player.username,
                                                            'entity': connected_player.character_entity,
                                                            'success': True, }))


class DistrictProcessor(esper.Processor):
    def process(self):
        (_, districts) = self.world.get_component(c.ActiveDistricts)[0]
        # districts = self.world.get_component(c.ActiveDistricts)
        current_districts = list(set(districts.active_districts))
        # print(current_districts)
        # districts.active_districts
        for ent, (person, position) in self.world.get_components(c.Person, c.Position):
            if person.is_player_controlled:
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
            districts_in_use, feed_district_offsets = mapManager.update_districts(districts.active_districts)
            # for district in districts.active_districts:
            #     self.world.create_entity(gs_map.Map(mapManager.districts_active_maps[district], district=district))
            entity_list = [[]] * 100
            for ent, (pos) in self.world.get_components(c.Position):
                # all entities that have a position, not all that necessarily are renderable
                if type(pos) == list: pos = pos[0]
                for enum, districts_to_update in enumerate(districts_in_use):
                    for district in districts_to_update:
                        if pos.district == enum:
                            temp_list = entity_list[district].copy()
                            temp_list.append((ent, pos.z, pos.y, pos.x, pos.district))
                            entity_list[district] = temp_list
            for district in districts.active_districts:
                maps.mapList[district] = gs_map.Map(mapManager.districts_active_maps[district], district=district,
                                                    entities=entity_list[district],
                                                    offsets=feed_district_offsets[district])


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
                # updated_fovs.append(ent) if the map isn't initialized yet, don't worry about it. will work next tick.
                continue

            # todo somehow register the entities that can see this one
            person.visible_entities = maps.mapList[position.district].calc_fov_ents(ent)
            # person.fov[0] = array of boolean grid visibility, [1] is horizontal walls, [2] is vertical walls
            if person.is_player_controlled:
                found_player = False
                for _, (connected_player) in self.world.get_component(c.ConnectedPlayer):
                    if connected_player.character_entity == ent:
                        found_player = True
                        break
                if found_player:
                    # todo get render information here

                    person.fov = maps.mapList[position.district].calc_fov_map(position.z, position.y, position.x,
                                                                              position.district)
                    asyncio.create_task(self.sio.emit('entities_update', to=connected_player.sid,
                                                      data={'data': json.dumps(person.visible_entities)}))
                    asyncio.create_task(self.sio.emit('map_update', to=connected_player.sid,
                                                      data={'data': json.dumps(person.fov)}))
            updated_fovs.append(ent)
        for _ in updated_fovs:
            self.world.remove_component(_, c.UpdateFov)

            pass
