import esper
from time import sleep
import socketio
import numpy as np
import random
import os
import psycopg2
import hashlib

import Components as c
import Processors
import websocket
import gs_map
import globalvar


# todo install heroku CLI

class Game:

    def __init__(self):

        self.world = esper.World()

        self.map = gs_map.MapManager()
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

        player = self.world.create_entity()
        self.world.add_component(player, c.Position(x=1, y=2))
        self.world.add_component(player, c.Velocity(x=1, y=-1))
        self.world.add_component(player,
                                 c.Renderable())  # always invoke component adds with () even if no constructor argument
        self.world.add_processor(Processors.MovementProcessor())

        # self.cursor.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
        # self.cursor.execute("SELECT * FROM test;")
        #
        # test = self.cursor.fetchall()
        # self.conn.commit()
        if os.environ['DATABASE_URL'].__contains__("localhost"):
            self.map._testmap()
        self.register(30000, {'username': 'epthed_test', 'password': 'password', 'email': 'epthedemail@gmail.com',
                              'admin': False})  # in prod I'll manually set admin users with db runs
        self.authenticate(3000, {'username': 'epthed_test', 'password': 'password'})

        names = ['John', 'Bob', 'Jimbo', 'Brick']
        for n in range(4):
            self.world.create_entity(c.Position(x=n, y=0), c.Velocity(x=1, y=1), c.Person(name=names[n]))

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
            return False
        self.conn.commit()
        return True

    def authenticate(self, sid, message):
        return True
