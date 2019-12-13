import asyncio
import datetime
import re
import time
import sqlite3

from ..Client import Client
from ..Log import Log
from ..SQL import SQL
from ..Singleton import Singleton

class POE_SQL(metaclass=Singleton):


    def __init__(self):
        self.client = Client()
        self.log = Log()
        self.ready = False
        self.sql = SQL()


    async def table_exists(self, table_name):
        cur = self.sql.conn.cursor()
        cmd = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        if cur.execute(cmd).fetchone():
            return True
        return False


    async def table_setup(self):
        """Setup any SQL tables needed for this class
        """
        while self.sql.ready == False:
            self.log.info("Sleep and wait")
            await asyncio.sleep(1)

        cur = self.sql.conn.cursor()

        self.log.info("Check to see if accounts exists.")
        if not await self.table_exists("accounts"):
            self.log.info("Create accounts table")
            cmd = """
                CREATE TABLE IF NOT EXISTS accounts
                (
                    account_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    created_at  INTEGER NOT NULL,
                    last_active INTEGER
                )"""
            cur.execute(cmd)
            await self.sql.commit()

        self.log.info("Check to see if characters exists.")
        if not await self.table_exists("characters"):
            self.log.info("Create characters table")
            # {'name': 'Sotonis', 'league': 'Standard', 'classId': 3, 'ascendancyClass': 2, 'class': 'Elementalist', 'level': 80, 'experience': 866729768, 'lastActive': True}
            cmd = """
                CREATE TABLE IF NOT EXISTS characters
                (
                    character_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id      INTEGER NOT NULL,
                    name            TEXT    NOT NULL,
                    league          TEXT    NOT NULL,
                    class_id         INTEGER NOT NULL,
                    ascendancy_class INTEGER NOT NULL,
                    class           TEXT    NOT NULL,
                    created_at      INTEGER NOT NULL,
                    last_active     INTEGER,
                    FOREIGN KEY(account_id) REFERENCES accounts(account_id)
                )"""
            cur.execute(cmd)
            await self.sql.commit()

        self.log.info("Check to see if experience exists.")
        if not await self.table_exists("experience"):
            self.log.info("Create experience table")
            # {'name': 'Sotonis', 'league': 'Standard', 'classId': 3, 'ascendancyClass': 2, 'class': 'Elementalist', 'level': 80, 'experience': 866729768, 'lastActive': True}
            cmd = """
                CREATE TABLE IF NOT EXISTS experience
                (
                    character_id    INTEGER NOT NULL,
                    level           INTEGER NOT NULL,
                    experience      INTEGER NOT NULL,
                    timestamp       INTEGER NOT NULL,
                    FOREIGN KEY(character_id) REFERENCES characters(character_id)
                )"""
            cur.execute(cmd)
            await self.sql.commit()


    async def register_account(self, name):
        """
        Write account information to db.
        This will also register all current characters!
        """
        cur = self.sql.conn.cursor()
        data = {}
        data['name'] = name
        data['created_at'] = time.time()
        data['last_active'] = None
        cmd = """INSERT OR FAIL INTO accounts
            (
                name,
                created_at,
                last_active
            ) VALUES (
                :name,
                :created_at,
                :last_active
            )
        """
        try:
            cur.execute(cmd, data)
            await self.sql.commit()
        except sqlite3.IntegrityError:
            return False
        return True


    async def iter_accounts(self):
        """
        Write account information to db
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT * FROM accounts"
        cur.execute(cmd)
        for account in  cur.fetchall():
            yield account

    async def get_account_id(self, account_name):
        """
        Read account_id information to db
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT account_id FROM accounts WHERE name = ?"
        cur.execute(cmd, (account_name,))
        return cur.fetchone()['account_id']


    async def register_character(self, char_dict, account_name):
        """
        Write character information to db
        """
        cur = self.sql.conn.cursor()
        data = {}
        data['account_id'] = await self.get_account_id(account_name)
        data['name'] = char_dict['name']
        data['league'] = char_dict['league']
        data['class_id'] = char_dict['classId']
        data['ascendancy_class'] = char_dict['ascendancyClass']
        data['class'] = char_dict['class']
        data['created_at'] = int(time.time())
        data['last_active'] = None
        cmd = """INSERT OR REPLACE INTO characters
            (
                account_id,
                name,
                league,
                class_id,
                ascendancy_class,
                class,
                created_at,
                last_active
            ) VALUES (
                :account_id,
                :name,
                :league,
                :class_id,
                :ascendancy_class,
                :class,
                :created_at,
                :last_active
            )
        """
        cur.execute(cmd, data)
        await self.write_xp(char_dict)
        await self.sql.commit()


    async def write_xp(self, char_dict):
        """
        Write character information to db
        """
        cur = self.sql.conn.cursor()
        data = {}
        data['character_id'] = await self.get_character_id(char_dict)
        data['timestamp'] = int(time.time())
        data['level'] = char_dict['level']
        data['experience'] = char_dict['experience']
        cmd = """INSERT OR REPLACE INTO experience
            (
                character_id,
                level,
                experience,
                timestamp
            ) VALUES (
                :character_id,
                :level,
                :experience,
                :timestamp
            )
        """
        cur.execute(cmd, data)
        await self.sql.commit()


    async def has_character(self, char_dict):
        """
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT * FROM characters WHERE name = ?"
        cur.execute(cmd, (char_dict['name'],))
        ret = cur.fetchall()
        if len(ret):
            return True
        return False

    async def get_character_id(self, char_dict):
        """
        Write character information to db
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT character_id FROM accounts WHERE name = ?"
        cur.execute(cmd, (char_dict['name'],))
        return cur.fetchone()['character_id']



        # TODO: Write function to get character XP