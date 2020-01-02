
import asyncio
import requests
import time

from . import POE_SQL, Account
from ..Client import Client
from ..Config import Config
from ..Log import Log
from ..SQL import SQL

class POE_Loop:

    influxDB_host = "http://192.168.4.3:8086"

    def __init__(self, args):
        self.log = Log()
        self.poe_sql = POE_SQL()
        self.args = args
        self.config = Config()

        self.sleep_time = self.config[self.args.env]['characters']['time_between_updates']


    async def loop(self):
        """
        Run the main loop of tracking various POE stuffs
        """
        self.log.info(f"Booted loop and sleeping for {self.sleep_time}s")
        while 1:
            # Check if we even need to follow characters
            if not self.config[self.args.env]['characters']['track']:
                self.log.warning("Config was set to not track characters. Aborting poe_loop.")
                break
            try:
                t1 = time.time()
                self.log.debug("Begin loop")
                async for account_dict in self.poe_sql.iter_accounts():
                    self.log.debug(f"Update account {account_dict['name']}")
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

                    # To save us from being blocked, check the headers and sleep away any needed delay
                    await self.sleep_for_state(a.headers['X-Rate-Limit-Ip'], a.headers['X-Rate-Limit-Ip-State'])

            except (KeyboardInterrupt, SystemExit, RuntimeError):
                raise
                return
            except requests.exceptions.HTTPError:
                self.log.exception("Caught HTTP error, sleep for 5 minutes.")
                await asyncio.sleep(300)
                continue
            except:
                self.log.exception("")

            # Calculate out loop processing time, and sleep the remainder
            # TODO: Doing this as a set time march would be better.
            sleep_time = max(0, self.sleep_time - (time.time() - t1))
            await asyncio.sleep(sleep_time)


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


    async def sleep_for_state(self, policies, states):
        """
        Given a policy (eg: 60:60:60, 60 requests allowed in 60 seconds with a 60 second block if exceeded)
        And a state (eg: 1:60:0, 1 request in the last 60 seconds with a 0 second timeout currently in effect)
        Async sleep as needed to prevent throttling
        'X-Rate-Limit-Ip': '60:60:60,200:120:900',
        'X-Rate-Limit-Ip-State': '1:60:0,1:120:0',
        We need to allow for complex policies if given them, such as this list seperated one!
        """
        sleep_needed = 0

        policy_lists = []
        for policy in policies.split(","):
            # self.log.info(f"Saw policy {policy}")
            policy_lists.append([int(i) for i in policy.split(":")])

        state_lists = []
        for state in states.split(","):
            # self.log.info(f"Saw state {state}")
            state_lists.append([int(i) for i in state.split(":")])

        for index in range(len(policy_lists)):
            # self.log.info(f"Parse {policy_lists[index]} against {state_lists[index]}")
            sleep_time = ((state_lists[index][0]/policy_lists[index][0])**10)*state_lists[index][1]
            sleep_needed = max(sleep_time, sleep_needed)
            # self.log.info(f"Need {sleep_time}")

        if sleep_needed > 1:
            self.log.info(f"Sleeping for {sleep_needed:.1f} to avoid character limits ")
        await asyncio.sleep(sleep_needed)
