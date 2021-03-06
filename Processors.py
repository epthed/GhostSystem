import esper
import Components as c
from numba import njit
# import socketio
# import websocket
import asyncio


# only implement processors for stuff that runs or needs to check every turn.
# regular functions are just fine for one-offs in your Game class
# great opportunity for multithreading here, launch off many copies of heavy operations like FoV and pathing.

class MovementProcessor(esper.Processor):

    # @njit('void(void)')
    def process(self):
        for ent, (vel, pos) in self.world.get_components(c.Velocity, c.Position):
            # pos.x += vel.x
            # pos.y += vel.y
            pos.x, pos.y = jitmovementprocessor(vel.x, vel.y, pos.x, pos.y)
            # print('movement', {'ent': ent, "x": pos.x, "y": pos.y})
            # message = 'movement', {'ent': ent, "x": pos.x, "y": pos.y}
            # if self.world.has_component(ent, c.Renderable):
            #     print(ent, "is renderable")
            # else:
            #     print(ent, "is not renderable")
            # asyncio.create_task(sio.emit('movement', {'ent': ent, "x": pos.x, "y": pos.y}))
            # asyncio create_task basically fires this off immediately.TODO sum up all the changes and broadcast at once

            # sio.my_event(sio.sid, message)


@njit()  # can use numba if you only pass in basic types. Passing in Component, not ok. Passing in specific values = ok
def jitmovementprocessor(velx, vely, posx, posy):
    posx += velx
    posy += vely
    return posx, posy
