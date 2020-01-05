
import asyncio
import requests
import httpx
import time
import datetime
import discord

from . import character_api, character_embeds, xp_math
from .. import mongo
from ...args import Args
from ...Config import Config
from ...Log import Log
from ...Client import Client
from pymongo import ReturnDocument

class Accounts_Loop:

    influxDB_host = "http://192.168.4.3:8086"

    def __init__(self):
        self.log = Log()
        self.args = Args()
        self.config = Config()
        self.stash_queue = asyncio.Queue()
        self.db = mongo.Mongo().db
        self.next_update = time.time()
        self.api = character_api.Character_Api()
        self.client = Client()

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
                try:
                    account_name, characters = await self.api.get_characters(account['accountName'])
                except (KeyboardInterrupt, SystemExit, RuntimeError):
                    raise
                except (KeyError, httpx.exceptions.HTTPError):
                    await asyncio.sleep(5)
                    continue

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
        now = datetime.datetime.utcnow()
        
        if db_character is None:
            db_character = await self.db.characters.find_one_and_update(
                {"name":character['name']},
                {
                    "$set": {
                        "accountName":account_name,
                        "lastActive":datetime.datetime.utcnow(),
                        "name": character["name"], 
                        "league": character["league"], 
                        "classId": character["classId"], 
                        "ascendancyClass": character["ascendancyClass"], 
                        "class": character["class"], 
                        "level": character["level"], 
                        "experience": character["experience"]
                    },
                    "$setOnInsert": 
                    {
                         "creationDate": now,
                         "stats": 
                         {
                             "total_experience": 0,
                             "lost_experience": 0,
                             "deaths": 0,
                             "playtime": 0,
                         },
                    }
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )

        db_xp = await self.db.characters.xp.find_one({"name": character['name']},sort=[('date',-1)])

        # Nothing to do if our local values still match
        if db_character['experience'] == character['experience'] and db_xp is not None:
            return

        self.log.info(f"Found active player {character['name']} (account_name)")

        await self.db.characters.xp.insert_one(
                {"name": character['name'],
                 "experience": character['experience'],
                 "level": character['level'],
                 "date": datetime.datetime.utcnow(),
                 "league": character['league'],
                }
        )

        deaths = 0
        if db_character['experience'] > character['experience']:
            old_percent = xp_math.XPMath().level_percent(db_character['experience'])
            new_percent = xp_math.XPMath().level_percent(character['experience'])
            deaths = old_percent - new_percent
            # 10% of xp is lost after the kitava fight. We kinda assume that 
            # anyone over level 60 is past that fight. 
            if character['level'] > 60:
                deaths /= 0.1
            else:
                deaths /= 0.05
            deaths = max(int(round(deaths)),1)

        lost_xp = max(0, db_character['experience'] - character['experience'])
        gained_xp = max(0, character['experience'] - db_character['experience'])
        if datetime.datetime.utcnow() - db_character['lastActive'] < datetime.timedelta(minutes=15):
            playtime = now - db_character['lastActive']
            playtime = playtime.total_seconds()
        else:
            playtime = 0

        # Pull the actual character JSON for use with deaths/dings
        lastActive = datetime.datetime.utcnow()
        updated_character = await self.db.characters.find_one_and_update(
                {"name":character['name']},
                {
                    "$set": 
                    {
                        "experience": character['experience'],
                        "level": character['level'],
                        "lastActive": now,
                    },
                    "$inc":
                    {
                        "stats.total_experince": gained_xp,
                        "stats.lost_expereince": lost_xp,
                        "stats.deaths": deaths,
                        "stats.playtime": playtime,
                    }
                },
                return_document=ReturnDocument.AFTER,
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

        # Handle any messages to discord
        if character['level'] != db_character['level']:
            if character['level'] > 50 or character['level'] % 5 == 0:
                # We had a ding!
                channel_id = self.config[self.args.env]['discord']['death_announces']
                if channel_id:
                    channel = self.client.get_channel(channel_id)
                    await channel.send(embed=character_embeds.ding_embed(updated_character))

        if deaths:
            channel_id = self.config[self.args.env]['discord']['death_announces']
            _filter = {
                    "name": character['name'],
                    "experience":{"$lte":character['experience']}, 
                    "date": {"$lt":now},
            }
            death_dict = await self.db.characters.xp.find_one(
                    _filter,
                    sort=[("date",-1)],
            )

            if channel_id:
                channel = self.client.get_channel(channel_id)
                await channel.send(embed=character_embeds.death_embed(updated_character, death_dict=death_dict))

        await self.post_char_to_influx(character, account_name)


    async def post_char_to_influx(self, char_dict, account_name):
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
        data += f"xp,env={self.args.env},name={char_dict['name']},league={char_dict['league']},class={char_dict['class']},account={account_name} level={char_dict['level']},total={char_dict['experience']}"
        self.log.debug(data)

        host = self.influxDB_host + '/write'
        params = {"db":"poe","precision":"m"}
        try:
            r = await httpx.post( host, params=params, data=data, timeout=1)
            r.raise_for_status()
            pass
            # print(data)
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            raise
            return
        except Exception as e:
            self.log.exception("Posting to InfluxDB threw exception")
            # continue
# .find(
# {
#     "name":"SotonBuffUm", 
#     "experience":{"$lte":1706027422}, 
#     "date": {"$lt":ISODate("2020-01-04T07:14:03.981-07:00") }
# })