import esper
from time import sleep
import socketio
import numpy as np
import random
import os
import psycopg2
# import hashlib
from argon2 import PasswordHasher, exceptions
import time
import string
from asyncio import CancelledError

import Components as c
import Processors
import websocket
import gs_map
import globalvar


class Game:

    def __init__(self):

        self.world = esper.World()
        self.stopping = False
        # self.map = gs_map.MapManager()
        # globalvar.cursor.execute(
        # "CREATE TABLE IF NOT EXISTS test (id serial PRIMARY KEY, num integer, data varchar);")
        globalvar.cursor.execute("CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY,"
                                 "username varchar UNIQUE,"
                                 "password varchar,"
                                 "email varchar,"
                                 "is_admin bool,"
                                 "auth_token varchar"
                                 ");")
        globalvar.cursor.execute("CREATE TABLE IF NOT EXISTS mapdata (id serial PRIMARY KEY,"
                                 "map json"  # stores json blob/string, will be a 3d numpy array
                                 ");")
        globalvar.cursor.execute("CREATE TABLE IF NOT EXISTS characters (id serial PRIMARY KEY,"
                                 "username varchar,"  # this username can run this character
                                 "charname varchar UNIQUE,"
                                 "char_data json"  # stores json blob/string, will be lots of stuff
                                 ");")
        globalvar.conn.commit()

    async def game_loop(self, sio, sanic, loop):

        self.world.create_entity(gs_map.MapManager())
        # always invoke component adds with () even if no constructor argument
        # self.world.add_component(player, c.Position(x=1, y=2))

        self.world.add_processor(Processors.MovementProcessor())
        self.world.add_processor(Processors.DistrictProcessor())
        self.world.add_processor(Processors.MapProcessor())
        self.world.add_processor(Processors.FovProcessor(sio=sio))

        # make the map handler
        self.world.create_entity(c.ActiveDistricts())
        self.world.create_entity(c.DistrictMaps())
        # self.cursor.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
        # self.cursor.execute("SELECT * FROM test;")
        #
        # test = self.cursor.fetchall()
        # self.conn.commit()
        if os.environ['DATABASE_URL'].__contains__("localhost"):  # todo these should be moved to a test suite
            self.new_character(300, {'userName': 'epthed_test', 'characterName': 'epthed'})  # create some characters
            self.new_character(30000, {'userName': 'epthed_test2', 'characterName': 'epthed2'})
            # (_, mapManager) = self.world.get_component(gs_map.MapManager)[0]
            # mapManager._testmap()

            self.register(30000, {'username': 'epthed_test', 'password': 'password', 'email': 'epthedemail@gmail.com',
                                  'admin': False})  # in prod I'll manually set admin users with db commands
            self.authenticate(3000, {'username': 'epthed_test', 'password': 'badpassword'})

        names = ['John', 'Bob', 'Jimbo', 'Brick', 'jones', 'jebediah']
        for n in range(6):  # create some NPCs
            self.world.create_entity(c.Position(x=n, y=n), c.Person(name=names[n]), c.UpdateFov(), c.Renderable())

        while True:
            try:
                start = time.time()
                self.world.process()
                end = time.time()
                if end - start > .01:
                    print("main loop took", round((end - start) * 1000, 3), "ms")
                # print("main thread tick")
                await sio.sleep(.1)
                # try to run at a 10 tickrate. Maybe? Gives the main thread 10 chances per second to do work
            except CancelledError:
                print("received shutdown signal, exited main game_loop")
                globalvar.conn.commit()
                globalvar.conn.close()
                return
            except Exception as e:
                print("unhandled exception during game loop")
                print(e)
                raise Exception(e)

        # os._exit(0)  # exits the entire program without throwing error, but doesn't cleanup web connections.

    def new_character(self, sid, message):
        ent = self.world.create_entity(c.Character(sid=sid, username=message['userName']),
                                       c.Position(district=random.randint(54, 56)), c.Renderable(),
                                       # c.Position(district=55), c.Renderable(),
                                       c.Person(name=message['characterName']), c.UpdateFov())
        return ent

    def stop(self):
        self.stopping = True

    def register(self, sid, message):
        ph = PasswordHasher(memory_cost=1000, parallelism=16)
        hashed_pw = ph.hash(message['password'].encode('utf-8'))
        hashed_email = ph.hash(message['email'].encode('utf-8'))
        rnd_lst = random.choices(string.ascii_letters, k=40)
        auth_token = "".join(rnd_lst)
        try:
            globalvar.cursor.execute("INSERT INTO users (username, password, email, is_admin, auth_token) "
                                     "VALUES (%s,%s,%s,%s, %s)", (message['username'], hashed_pw, hashed_email,
                                                                  False, auth_token))
        except psycopg2.errors.UniqueViolation:
            globalvar.conn.rollback()
            return False
        globalvar.conn.commit()
        return auth_token, message['username']

    def authenticate(self, sid, message):
        ph = PasswordHasher(memory_cost=1000, parallelism=16)
        username = message['username']
        if 'password' in message:
            provided_pw = message['password']
        else:
            provided_pw = None
        if 'auth_token' in message:
            auth_token = message['auth_token']
        else:
            rnd_lst = random.choices(string.ascii_letters, k=40)
            auth_token = "".join(rnd_lst)
        try:
            globalvar.cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user_object = globalvar.cursor.fetchone()
            if user_object is None: raise TypeError
        except TypeError:
            globalvar.conn.rollback()
            return False  # user doesn't exist
        stored_pw = user_object[2]
        stored_auth_token = user_object[5]
        if provided_pw:
            try:
                if ph.verify(stored_pw, provided_pw):
                    globalvar.cursor.execute("UPDATE users SET auth_token = %s WHERE username=%s",
                                             (auth_token, username,))
                    globalvar.conn.commit()
                    self.world.create_entity(c.Character(sid=sid, username=username))
                    return auth_token, username  # success
            except exceptions.VerifyMismatchError:
                return False  # password fail
        else:  # validate based on provided auth token
            if stored_auth_token == auth_token:
                return auth_token, username
            else:
                return False
