from sanic import Sanic
import asyncio
import socketio
import os

from game_root import Game

# mgr = socketio.AsyncRedisManager('redis://')
sio = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins=os.environ.get('ORIGINS'), logger=True,
                           engineio_logger=True)  # ,client_manager=mgr)
goFast = Sanic(name="GhostSystem Local")
sio.attach(goFast)
game = Game()


@goFast.listener('before_server_start')
def before_server_start(sanic, loop):
    sio.start_background_task(game.game_loop, sio, sanic, loop)


@sio.event
async def my_event(sid, message):
    await sio.emit('my_response', {'data': message['data']}, room=sid)


@sio.event
async def my_broadcast_event(sid, message):
    await sio.emit('my_response', {'data': message['data']})


@sio.event
async def join(sid, message):
    sio.enter_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Entered room: ' + message['room']},
                   room=sid)


@sio.event
async def leave(sid, message):
    sio.leave_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Left room: ' + message['room']},
                   room=sid)


@sio.event
async def close_room(sid, message):
    await sio.emit('my_response',
                   {'data': 'Room ' + message['room'] + ' is closing.'},
                   room=message['room'])
    await sio.close_room(message['room'])


@sio.event
async def my_room_event(sid, message):
    await sio.emit('my_response', {'data': message['data']},
                   room=message['room'])


@sio.event
async def disconnect_request(sid):
    await sio.disconnect(sid)


@sio.event
async def connect(sid, environ):
    print("Client", sid, "connected")
    await sio.emit('my_response', {'data': 'Connected', 'count': 0}, room=sid)


@sio.event
def disconnect(sid):
    print('Client disconnected')


@sio.event
async def new_character(sid, message):
    game.new_character(sid, message)
    await sio.emit('new_character', {'message': "Character " + message + " was created", 'characterName': message},
                   room=sid)
