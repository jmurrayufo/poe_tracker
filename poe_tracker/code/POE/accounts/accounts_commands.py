
from ...args import Args
from ...Log import Log
from .. import mongo
from . import character_api, plotter
import datetime
from pymongo import ReturnDocument
import re



class Accounts_Commands:

    def __init__(self):

        self.log = Log()
        self.ready = False
        self.db = mongo.Mongo().db
        self.args = Args()
        self.api = character_api.Character_Api()

    async def test(self, args):
        from . import character_embeds
        self.log.info(f"Ran test with {args}")
        """
        Namespace(cmd=<bound method Accounts_Commands._cmd_test of <poe_tracker.code.POE.accounts.accounts_commands.Accounts_Commands object at 0x7fac95c89990>>, league=None, message=<Message id=662204499120881674 channel=<TextChannel id=606974927308062750 name='bot_spam' position=2 nsfw=False news=False category_id=None> type=<MessageType.default: 0> author=<Member id=185846097284038656 name='Soton' discriminator='2585' bot=False nick='John' guild=<Guild id=346094316428591104 name='IsBe' shard_id=None chunked=True member_count=61>>>)
        """
        character = await self.db.characters.find_one({"name" : "SotonShockUm"})
        em = character_embeds.ding_embed(character)
        await args.message.channel.send(embed=em)
        em = character_embeds.death_embed(character)
        await args.message.channel.send(embed=em)
        

    async def register(self, args):
        """Attempt to register an account
        """
        self.log.info(f"Attempting to register an account")
        account_name, characters = await self.api.get_characters(args.account)

        # If we didn't find what we were looking for, bail out
        if account_name is None:
            await args.message.channel.send(f"I cannot find an account/character under the name of {args.account}. Check spelling and try again?")
            return

        # Notify our user if this is a re-registration
        doc = await self.db.accounts.find_one({"accountName":account_name})
        if doc:
            await args.message.channel.send(f"I already have this account, linking it to your discord and updating characters now.")

        # Check to see if this account is on the mongo DB
        doc = await self.db.accounts.find_one_and_update(
            {"accountName":account_name},
            {   
                "$set": { 
                    "accountName":account_name,
                    "discordId":args.message.author.id,
                    "lastActive":datetime.datetime.utcnow() 
                },
                "$setOnInsert": { 
                    "registrationDate":datetime.datetime.utcnow(),
                    "stats": { 
                        "total_experience": 0,
                        "lost_experience": 0,
                        "deaths": 0,
                        "playtime": 0
                    },
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        for character in characters:
            self.log.debug(character)
            await self.db.characters.find_one_and_update(
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
                         "creationDate":datetime.datetime.utcnow(),
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
        await args.message.channel.send(f"I have registered `{account_name}` to <@{args.message.author.id}>")


    async def plot(self, args):
        """
        Grab characters from the SQL db and give to the plotting class
        Note: Some filtering happens in the Plotter (such as time filters!)
            "names",
            "--differential","-d",
            "--league", "-l",
            "--recent", "-r",
        """
        self.log.info("Check if character even exists")

        characters = []
        for char_name in args.names:
            char_dict = await self.db.characters.find_one({"name":char_name})
            if char_dict is None:
                continue
            # We only add the *name* here. Why? Becuase then filtering is easier, and we can just get the
            # correct dicts later!
            characters.append(char_dict['name'])


        # if args.all:
        #     if not await self.poe_sql.has_character_by_name(char_name):
        #         # await args.message.channel.send("Character not found.")
        #         # return
        #         continue

        #     char_dict = await self.poe_sql.get_character_dict_by_name(char_name)
        #     c = Character(char_dict, None)
        #     characters.append(c)
        #     self.log.info(f"Appended {c}")
            


        # If we didn't get any names, maybe we were just asked to filter a league?
        if args.league is not None:
            chars = await self.db.characters.find({"league":re.compile(args.league)})
            chars = chars.to_list()
            for char in chars:
                if char['name'] not in characters:
                    characters.append(char['name'])

        if not len(characters):
            await args.message.channel.send("I need chracters to plot!")
            return

        await plotter.Plotter().plot_character(args, characters)


    async def leaderboard(self, args):
        self.log.info("Print leaderboard")
        """
            "--league", "-l",
            "--account", "-a",
            "--recent", "-r",
            "--top", "-t",
        """
        mongo_filter = {}
        if args.league:
            mongo_filter['league'] = re.compile(args.league)
        if args.account:
            mongo_filter['account'] = re.compile(args.account)
        if args.recent:
            mongo_filter['lastActive'] = {"$gt": datetime.datetime.utcnow() - datetime.timedelta(hours=args.recent)}

        self.log.info(mongo_filter)
        cursor = self.db.characters.find(mongo_filter,sort=[("experience",-1)])
        chars = await cursor.to_list(args.top)

        message = "Top Characters:\n```\n"
        rank = 1
        for char in chars:
            char_and_account = f"{char['name']} ({char['accountName']})"
            message += f"{rank}) {char_and_account:>36} XP: {char['experience']:,} (Level:{char['level']}) \n"
            rank += 1
        message += "```"
        await args.message.channel.send(message)


    async def list(self, args):
        """
        "--league LEAGUE",
        "--recent",
        "--account ACCOUNT",
        """
        message = "```\n"
        async for char in self.poe_sql.iter_characters():
            # self.log.info(char)
            # em.add_field(name=char['aname'], value=char['name'])
            if args.league and args.league in char['league'].lower():
                message += f"{char['name']:20} ({char['ac_name']})\n"
            elif args.league is None:
                message += f"{char['name']:20} ({char['ac_name']})\n"

            if len(message) > 1900:
                message += "```"
                await args.message.author.send(message)
                message = "```\n"


        message += "```"
        await args.message.author.send(message)
        await args.message.channel.send("Lists are big, check your DMs.")
