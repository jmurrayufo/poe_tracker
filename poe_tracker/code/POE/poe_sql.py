import asyncio
import datetime
import re
import sqlite3
import time

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
                    UNIQUE(character_id, experience),
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


    async def register_character(self, character):
        """
        Write character information to db
        """
        cur = self.sql.conn.cursor()
        data = {}
        data['account_id'] = await self.get_account_id(character.account.name)
        data['name'] = character.name
        data['league'] = character.league
        data['class_id'] = character.classId
        data['ascendancy_class'] = character.ascendancyClass
        data['class'] = character._class
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
        await self.write_xp(character)
        await self.sql.commit()


    async def has_character(self, character):
        """
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT * FROM characters WHERE name = ?"
        cur.execute(cmd, (character.name,))
        ret = cur.fetchall()
        if len(ret):
            return True
        return False    


    async def has_character_by_name(self, name):
        """
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT * FROM characters WHERE name = ?"
        cur.execute(cmd, (name,))
        ret = cur.fetchall()
        if len(ret):
            return True
        return False


    async def get_character_dict_by_name(self, name):
        """
        Return a character dict, formatted just like POE would have given us.
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT * FROM characters WHERE name = ?"
        cur.execute(cmd, (name,))
        ret = cur.fetchone()
        char_dict = {}
        char_dict['name'] = ret['name']
        char_dict['league'] = ret['league']
        char_dict['classId'] = ret['class_id']
        char_dict['ascendancyClass'] = ret['ascendancy_class']
        char_dict['class'] = ret['class']
        char_dict['level'] = 0
        char_dict['experience'] = 0
        return char_dict


    async def get_character_id(self, character):
        """
        Write character information to db
        """
        cur = self.sql.conn.cursor()
        cmd = "SELECT character_id FROM characters WHERE name = ?"
        cur.execute(cmd, (character.name,))
        return cur.fetchone()['character_id']


    async def iter_characters(self):
        cur = self.sql.conn.cursor()
        cmd = "SELECT *,ch.name as name,ac.name AS ac_name FROM characters ch INNER JOIN accounts ac on ch.account_id = ac.account_id"
        for row in cur.execute(cmd):
            yield row


    async def get_character_last_xp(self, character):
        cur = self.sql.conn.cursor()
        cmd = """
        SELECT 
            * 
        FROM 
            experience xp 
        INNER JOIN 
            characters ch ON xp.character_id = ch.character_id 
        WHERE 
            ch.name = ? 
        ORDER BY 
            timestamp DESC 
        LIMIT 1"""
        cur.execute(cmd, (character.name,))
        return cur.fetchone()


    async def write_xp(self, character):
        """
        Write xp information to db
        This will silently fail if information is already in DB
        """
        cur = self.sql.conn.cursor()
        data = {}
        data['character_id'] = await self.get_character_id(character)
        data['timestamp'] = int(time.time())
        data['level'] = character.level
        data['experience'] = character.experience
        cmd = """INSERT OR IGNORE INTO experience
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
        if cur.rowcount:
            await self.sql.commit()
        return cur.rowcount


    async def iter_character_xp(self, character, start=None, end=None):
        """
        Async iteration of the characters xp
            start: starting timestamp, entries must be above this
            end: ending timestamp, entries must be under this
        """
        cur = self.sql.conn.cursor()
        cmd = """SELECT timestamp, experience, level FROM experience xp INNER JOIN characters ch ON xp.character_id = ch.character_id WHERE ch.name = ? ORDER BY timestamp"""
        for row in cur.execute(cmd, (character.name,)):
            yield row
            await asyncio.sleep(0)
