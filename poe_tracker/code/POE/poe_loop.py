
import asyncio
import requests

from ..Client import Client
from ..Log import Log
from ..SQL import SQL
from . import POE_SQL, Account

class POE_Loop:


    def __init__(self, sleep_time=300):
        self.sleep_time = sleep_time
        self.log = Log()
        self.poe_sql = POE_SQL()


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted loop and sleeping for {self.sleep_time}s")
        while 1:
            self.log.info("LOOP!")
            async for account_dict in self.poe_sql.iter_accounts():
                self.log.info(account_dict)
                a = Account(account_dict['name'])
                for character in a.iter_characters():
                    # self.log.info(character)
                    if not await self.poe_sql.has_character(character):
                        self.log.info("Register a new char!")
                        await self.poe_sql.register_character(character, account_dict['name'])
            
            await asyncio.sleep(self.sleep_time)
