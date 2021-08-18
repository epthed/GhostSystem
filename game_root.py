import json
import os
import pickle
import random
import string
import time
from asyncio import CancelledError

import esper
import psycopg2
# import hashlib
from argon2 import PasswordHasher, exceptions

import Components as c
import Processors
import globalvar
import gs_map


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
                                 "char_data bytea"  # stores json blob/string, will be lots of stuff
                                 ");")
        globalvar.conn.commit()

    async def game_loop(self, sio, sanic, loop):

        self.world.create_entity(gs_map.MapManager())
        # always invoke component adds with () even if no constructor argument
        # self.world.add_component(player, c.Position(x=1, y=2))

        self.world.add_processor(Processors.MovementProcessor(), priority=5)
        self.world.add_processor(Processors.MapProcessor(), priority=4)
        self.world.add_processor(Processors.DistrictProcessor(), priority=3)
        self.world.add_processor(Processors.LoginProcessor(game=self, sio=sio))
        self.world.add_processor(Processors.FovProcessor(sio=sio), priority=2)

        # make the map handler
        self.world.create_entity(c.ActiveDistricts())
        self.world.create_entity(c.DistrictMaps())
        # self.cursor.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
        # self.cursor.execute("SELECT * FROM test;")
        #
        # test = self.cursor.fetchall()
        # self.conn.commit()
        self.register(30000,
                      {'username': 'epthed_test', 'password': 'passwordpassword', 'email': 'epthedemail@gmail.com',
                       'admin': False})
        if os.environ['DATABASE_URL'].__contains__("localhost"):  # todo these should be moved to a test suite
            self.new_character(0, {'username': 'epthed_test', 'characterName': 'epthed'})  # create some characters
            self.new_character(0, {'username': 'epthed_test2', 'characterName': 'epthed2'})
            # (_, mapManager) = self.world.get_component(gs_map.MapManager)[0]
            # mapManager._testmap()

            self.register(30000, {'username': 'epthed_test', 'password': 'password', 'email': 'epthedemail@gmail.com',
                                  'admin': False})  # in prod I'll manually set admin users with db commands
            self.authenticate(3000, {'username': 'epthed_test', 'password': 'badpassword'})

        # names = ['John', 'Bob', 'Jimbo', 'Brick', 'jones', 'jebediah']
        for n in range(40, 69):  # create some NPCs
            self.world.create_entity(c.Position(x=0, y=0, district=n), c.Person(name=str(n)), c.UpdateFov(),
                                     c.Renderable())

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
                for ent, (connected_player) in self.world.get_component(c.ConnectedPlayer):
                    self.client_disconnect(connected_player.sid)
                globalvar.conn.commit()
                globalvar.conn.close()
                return
            except Exception as e:
                print("unhandled exception during game loop")
                print(e)
                raise Exception(e)

        # os._exit(0)  # exits the entire program without throwing error, but doesn't cleanup web connections.

    def new_character(self, sid, message):
        npc = False
        if sid == 0:  # this is an npc or internal creation
            npc = True
            message['username'] = ''
        connected_player_outer = None
        for ent, (connected_player) in self.world.get_component(c.ConnectedPlayer):
            if connected_player.sid == sid:
                connected_player.charName = message['characterName']
                connected_player_outer = connected_player
                break  # we now have the player who requested this creation
        try:
            globalvar.cursor.execute("INSERT INTO characters (username, charname, char_data) "
                                     "VALUES (%s,%s,%s)",
                                     (message['username'], message['characterName'], json.dumps({})))
        except psycopg2.errors.UniqueViolation:
            globalvar.conn.rollback()
            return False
        ent = self.world.create_entity(c.Position(district=random.randint(54, 56)), c.Renderable(),
                                       c.Person(name=message['characterName'], is_player_controlled=not npc),
                                       c.UpdateFov())

        if not npc: connected_player_outer.character_entity = ent
        self.save_character(ent)
        self.world.create_entity(c.UpdateMap())
        return ent

    def save_character(self, ent):
        person = self.world.component_for_entity(ent, c.Person)
        person.fov = None  # null out big stuff we don't want to store persistently
        character_data = pickle.dumps(self.world.components_for_entity(ent))
        globalvar.cursor.execute("UPDATE characters SET char_data = %s WHERE charname=%s",
                                 (character_data, person.name,))
        globalvar.conn.commit()

    def load_character(self, charname):
        try:
            globalvar.cursor.execute("SELECT char_data FROM characters WHERE charname=%s", (charname,))
            char_object = globalvar.cursor.fetchone()
            if char_object is None: raise TypeError
        except TypeError:
            globalvar.conn.rollback()
            return False  # character does not exist
        char_data = char_object[0]
        ent = self.world.create_entity(*pickle.loads(char_data), c.UpdateFov())
        self.world.create_entity(c.UpdateMap())  # also fire off an updatemap
        return ent

    def client_disconnect(self, sid):
        for ent, (connected_player) in self.world.get_component(c.ConnectedPlayer):
            if connected_player.sid == sid and connected_player.character_entity != 0:
                self.save_character(connected_player.character_entity)
                self.world.delete_entity(connected_player.character_entity)
                self.world.delete_entity(ent)
                self.world.create_entity(c.UpdateMap())
                break

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
                    self.world.create_entity(c.ConnectedPlayer(sid=sid, username=username))
                    return auth_token, username  # success
            except exceptions.VerifyMismatchError:
                return False  # password fail
        else:  # validate based on provided auth token
            if stored_auth_token == auth_token:
                self.world.create_entity(c.ConnectedPlayer(sid=sid, username=username))
                return auth_token, username
            else:
                return False
