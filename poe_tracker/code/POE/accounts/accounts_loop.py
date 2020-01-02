
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
                self.log.info(f"Update {account['accountName']}")
                account_name, characters = await self.api.get_characters(account['accountName'])
                if account_name is None:
                    continue
                for character in characters:
                    await asyncio.sleep(0)
                    self.log.info(f"Update {character}")

            self.next_update += self.config[self.args.env]['characters']['time_between_updates']


            

