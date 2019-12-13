
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
            try:
                self.log.debug("Begin loop")
                async for account_dict in self.poe_sql.iter_accounts():
                    a = Account(account_dict['name'])
                    for character in a.iter_characters():
                        if not await self.poe_sql.has_character(character):
                            self.log.info(f"Register a new character {character} under {a}")
                            await self.poe_sql.register_character(character)
                        else:
                            db_char_dict = await self.poe_sql.get_character_last_xp(character)
                            changes = await self.poe_sql.write_xp(character)
                            if changes:
                                self.log.info(f"XP infomation updated for {character}")
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.log.exception("")

            await asyncio.sleep(self.sleep_time)
