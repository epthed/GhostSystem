import esper
from time import sleep
import socketio
import numpy as np
import random

import Components as c
import Processors
import websocket
import gs_map


# todo install heroku CLI
# todo change to conda environment from pyenv. then change buildrunner in heroku

class Game:

    def __init__(self):
        self.world = esper.World()

    async def game_loop(self, sio, sanic, loop):

        player = self.world.create_entity()
        self.world.add_component(player, c.Position(x=1, y=2))
        self.world.add_component(player, c.Velocity(x=1, y=-1))
        self.world.add_component(player,
                                 c.Renderable())  # always invoke component adds with () even if no constructor argument
        self.world.add_processor(Processors.MovementProcessor())
        map = self.create_test_map()

        for n in range(1):
            self.world.create_entity(c.Position(x=n, y=n), c.Velocity(x=1, y=1))

        print(self.world.components_for_entity(player))
        print(self.world.has_component(player, c.Position))

        while True:
            self.world.process()
            await sio.sleep(1)  # try to run at a 10 tickrate? Maybe? Gives the main thread 10 chances per second to do
            # network IO stuff

            # print("world tick")

    def new_character(self, sid, message):
        self.world.create_entity(c.SessionId(sid=sid), c.Position(), c.Velocity(), c.Renderable(),
                                 c.Person(name=message))

    def create_test_map(self):
        # only display thin walls at render time. Keep memory Map as expanded.
        # Only even/even tiles are the "real" tiles, others are representative of walls/corners
        # from this map object we derive the tcod concepts of fov_map and navigation map

        map = [[[gs_map.Tile() for col in range(10)] for col in range(10)] for row in
               range(2)]  # y, x, z? 0,0 is top left
        for zSlice in map:  # z iteration, outside in
            for idx, xSlice in enumerate(zSlice):
                for idy, cell in enumerate(xSlice):
                    if idx % 2 == 0 and idy % 2 == 0:
                        cell.spatial = True
        print(map)
        return map
