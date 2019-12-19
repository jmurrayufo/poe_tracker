
import asyncio
import requests

from ..Client import Client
from ..Log import Log
from ..SQL import SQL
from . import POE_SQL, Account

class POE_Loop:

    influxDB_host = "http://192.168.4.3:8086"

    def __init__(self, sleep_time=300, args=None):
        self.sleep_time = sleep_time
        self.log = Log()
        self.poe_sql = POE_SQL()
        self.args = args


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted loop and sleeping for {self.sleep_time}s")
        while 1:
            try:
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
                        await self.post_char_to_influx(character)
            except (KeyboardInterrupt, SystemExit, RuntimeError):
                raise
                return
            except requests.exceptions.HTTPError:
                self.log.exception("Caught HTTP error, sleep.")
                continue
            except:
                self.log.exception("")
            finally:
                await asyncio.sleep(self.sleep_time)


    async def post_char_to_influx(self, character):
        pass
        """        
        self.name = char_dict['name']
        self.league = char_dict['league']
        self.classId = char_dict['classId']
        self.ascendancyClass = char_dict['ascendancyClass']
        self._class = char_dict['class']
        self.level = char_dict['level']
        self.experience = char_dict['experience']
        self.account = account
        """

        data = ""
        data += f"xp,env={self.args.env},name={character.name},league={character.league},class={character._class},account={character.account.name} level={character.level},total={character.experience}"
        self.log.debug(data)

        host = self.influxDB_host + '/write'
        params = {"db":"poe","precision":"m"}
        try:
            r = requests.post( host, params=params, data=data, timeout=1)
            pass
            # print(data)
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            raise
            return
        except Exception as e:
            self.log.exception("Posting to InfluxDB threw exception")
            # continue
