
import asyncio
import requests
import httpx
import time
import datetime

from ...Config import Config
from ...Log import Log
from .. import mongo
from ...args import Args
from . import character_api

class Accounts_Loop:

    def __init__(self):
        self.log = Log()
        self.args = Args()
        self.config = Config()
        self.stash_queue = asyncio.Queue()
        self.db = mongo.Mongo().db
        self.next_update = time.time()
        self.api = character_api.Character_Api()

    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted Accounts_Loop")
        while 1:
            # Check if we even need to follow characters
            if not self.config[self.args.env]['characters']['track']:
                self.log.warning("Config was set to not track characters. Aborting poe_loop.")
                break
            
            while time.time() < self.next_update:
                await asyncio.sleep(1)

            async for account in self.db.accounts.find():
                self.log.debug(f"Update {account['accountName']}")
                account_name, characters = await self.api.get_characters(account['accountName'])
                if account_name is None:
                    continue
                for character in characters:
                    await asyncio.sleep(0)
                    self.log.debug(f"Update {character}")
                    await self.update_character(account_name, character)

                    #stuff = await self.api.get_items(account_name, character['name'])
                    #print(stuff)
                    #exit()

            self.next_update += self.config[self.args.env]['characters']['time_between_updates']


    async def update_character(self, account_name, character):
        db_account = await self.db.accounts.find_one({"accountName":account_name})
        db_character = await self.db.characters.find_one({"name":character['name']})
        db_xp = await self.db.characters.xp.find_one({"name": character['name']},sort=[('date',-1)])

        # Nothing to do if our local values still match
        if db_character['experience'] == character['experience'] and db_xp is not None:
            return

        self.log.info(f"Found active player {character['name']} (account_name)")

        await self.db.characters.xp.insert_one(
                {"name": character['name'],
                 "experience": character['experience'],
                 "level": character['level'],
                 "date": datetime.datetime.now(),
                 "league": character['league'],
                }
            )

        deaths = 1 if db_character['experience'] > character['experience'] else 0
        lost_xp = max(0, db_character['experience'] - character['experience'])
        gained_xp = max(0, character['experience'] - db_character['experience'])
        if datetime.datetime.utcnow() - db_character['lastActive'] < datetime.timedelta(minutes=15):
            playtime = datetime.datetime.utcnow() - db_character['lastActive']
            playtime = playtime.total_seconds()
        else:
            playtime = 0


        await self.db.characters.find_one_and_update(
            {"name":character['name']},
            {
                "$set": 
                {
                    "experience": character['experience'],
                    "level": character['level'],
                    "lastActive": datetime.datetime.utcnow(),
                },
                "$inc":
                {
                    "stats.total_experince": gained_xp,
                    "stats.lost_expereince": lost_xp,
                    "stats.deaths": deaths,
                    "stats.playtime": playtime,
                }
            }
        )


        await self.db.accounts.find_one_and_update(
            {"accountName":account_name},
            {
                "$inc":
                {
                    "stats.total_experince": gained_xp,
                    "stats.lost_expereince": lost_xp,
                    "stats.deaths": deaths,
                    "stats.playtime": playtime,
                }
            }
        )

