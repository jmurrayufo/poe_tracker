
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
                await asyncio.sleep(self.sleep_time)
                self.log.debug("Begin loop")
                async for account_dict in self.poe_sql.iter_accounts():
                    self.log.debug(f"Update account {account_dict['name']}")
                    # I suspect the API hates us jamming in lots of requests, lets pause while we loop.
                    await asyncio.sleep(2)
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
            except (KeyboardInterrupt, SystemExit, RuntimeError):
                raise
                return
            except requests.exceptions.HTTPError:
                self.log.exception("Caught HTTP error, sleep.")
                continue
            except:
                self.log.exception("")

