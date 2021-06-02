from sanic import Sanic
from sanic.response import redirect
from threading import Thread
import asyncio
import socketio
import os
from time import sleep

from game_root import Game

# mgr = socketio.AsyncRedisManager('redis://')
sio = socketio.asyncio_server.AsyncServer(async_mode='sanic', cors_allowed_origins=os.environ.get('ORIGINS'),
                                          logger=True,
                                          engineio_logger=True)  # ,client_manager=mgr)
print("Async server started, accepting connections from", os.environ.get('ORIGINS'), "on port", os.environ.get('PORT'))
goFast = Sanic(name="GhostSystem Local")
sio.attach(goFast)
game = Game()


# todo graceful handling of sigterm


@goFast.get('/')
async def handler(request):
    return redirect("https://ghostsystem-web.herokuapp.com/")


@goFast.listener('before_server_start')
def before_server_start(sanic, loop):
    goFast.add_task(game.game_loop(sio, sanic, loop))


@goFast.listener('before_server_stop')
def before_server_stop(sanic, loop):
    print("got nice stop, trying to stop the background thread")
    game.stop()


@goFast.listener('main_process_stop')
def main_process_stop(sanic, loop):
    print("main process ending after nice stop")  # ends up not called, not a big deal
    # look here if nicer end needed https://stackoverflow.com/questions/37417595/graceful-shutdown-of-asyncio-coroutines


@sio.event
async def my_event(sid: str, message: dict):
    await sio.emit('my_response', {'data': message['data']}, room=sid)


@sio.event
async def my_broadcast_event(sid: str, message: dict):
    await sio.emit('my_response', {'data': message['data']})


@sio.event
async def join(sid: str, message: dict):
    sio.enter_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Entered room: ' + message['room']},
                   room=sid)


@sio.event
async def leave(sid: str, message: dict):
    sio.leave_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Left room: ' + message['room']},
                   room=sid)


@sio.event
async def close_room(sid: str, message: dict):
    await sio.emit('my_response',
                   {'data': 'Room ' + message['room'] + ' is closing.'},
                   room=message['room'])
    await sio.close_room(message['room'])


@sio.event
async def my_room_event(sid: str, message: dict):
    await sio.emit('my_response', {'data': message['data']},
                   room=message['room'])


@sio.event
async def disconnect_request(sid: str):
    await sio.disconnect(sid)


@sio.event
async def connect(sid: str, environ):
    print("Client", sid, "connected")
    await sio.emit('my_response', {'data': 'Connected', 'count': 0}, room=sid)


@sio.event
def disconnect(sid: str):
    print('Client disconnected', sid)


@sio.event
async def new_character(sid: str, message: dict):
    game.new_character(sid, message)
    await sio.emit('new_character',
                   {'message': "Character " + message['characterName'] + " was created for user " + message['userName'],
                    'characterName': message['characterName']}, room=sid)


@sio.event
async def register(sid: str, message: dict):
    success = game.register(sid, message)
    if success:
        await sio.emit('register', {'message': "User " + message + " was created", 'success': success}, room=sid)
    else:
        await sio.emit('register', {'message': "Registration Failed", 'success': success}, room=sid)


@sio.event
async def authenticate(sid: str, message: dict):
    success = game.authenticate(sid, message)
    if success:
        await sio.emit('authenticate', {'message': "Welcome back " + message.username + ".", 'success': success},
                       room=sid)
    else:
        await sio.emit('authenticate', {'message': "Authentication Failed", 'success': success}, room=sid)
