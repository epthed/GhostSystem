import esper
from time import sleep
import socketio
import numpy as np
import random
import os
import psycopg2
import hashlib
import time

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
        globalvar.cursor.execute("CREATE TABLE IF NOT EXISTS test (id serial PRIMARY KEY, num integer, data varchar);")
        globalvar.cursor.execute("CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY,"
                                 "username varchar UNIQUE,"
                                 "password bytea,"
                                 "email bytea,"
                                 "salt bytea,"
                                 "is_admin bool"
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

        # make the map handler
        self.world.create_entity(c.ActiveDistricts())
        # self.cursor.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
        # self.cursor.execute("SELECT * FROM test;")
        #
        # test = self.cursor.fetchall()
        # self.conn.commit()
        if os.environ['DATABASE_URL'].__contains__("localhost"):
            self.new_character(300, {'userName': 'epthed_test', 'characterName': 'epthed'})
            self.new_character(30000, {'userName': 'epthed_test2', 'characterName': 'epthed2'})
            # (_, mapManager) = self.world.get_component(gs_map.MapManager)[0]
            # mapManager._testmap()

            self.register(30000, {'username': 'epthed_test', 'password': 'password', 'email': 'epthedemail@gmail.com',
                                  'admin': False})  # in prod I'll manually set admin users with db runs
            self.authenticate(3000, {'username': 'epthed_test', 'password': 'password'})

        names = ['John', 'Bob', 'Jimbo', 'Brick']
        for n in range(4):
            self.world.create_entity(c.Position(x=n, y=0), c.Person(name=names[n]))

        while not self.stopping:
            start = time.time()
            self.world.process()
            end = time.time()
            if end - start > .01:
                print("main loop took", round((end - start) * 1000, 3), "ms")
            # print("main thread tick")
            await sio.sleep(.1)  # try to run at a 10 tickrate? Maybe? Gives the main thread 10 chances per second to do

        print("received shutdown signal, exited main game_loop")
        # todo add graceful shutdown stuff here
        globalvar.conn.commit()
        globalvar.conn.close()
        os._exit(0)  # exits the entire program without throwing error, but doesn't cleanup web connections.

    def new_character(self, sid, message):
        self.world.create_entity(c.Character(sid=sid, username=message['userName']),
                                 c.Position(district=random.randint(0, 99)), c.Renderable(),
                                 c.Person(name=message['characterName']))

    def stop(self):
        self.stopping = True

    def register(self, sid, message):
        salt = os.urandom(16)
        hashed_pw = hashlib.pbkdf2_hmac('sha512', password=message['password'].encode('utf-8'),
                                        salt=salt, iterations=1000)
        hashed_email = hashlib.pbkdf2_hmac('sha512', password=message['email'].encode('utf-8'),
                                           salt=salt, iterations=1000)
        try:
            globalvar.cursor.execute("INSERT INTO users (username, password, email, salt, is_admin) "
                                     "VALUES (%s,%s,%s,%s,%s)", (message['username'], hashed_pw, hashed_email, salt,
                                                                 False))
        except psycopg2.errors.UniqueViolation:
            globalvar.conn.rollback()
            return False
        globalvar.conn.commit()
        return True

    def authenticate(self, sid, message):
        return True
