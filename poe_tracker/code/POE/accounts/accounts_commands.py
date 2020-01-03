
from ...args import Args
from ...Log import Log
from .. import mongo
from . import character_api
import datetime
from pymongo import ReturnDocument



class Accounts_Commands:

    def __init__(self):

        self.log = Log()
        self.ready = False
        self.db = mongo.Mongo().db
        self.args = Args()
        self.api = character_api.Character_Api()

    async def test(self, args):
        self.log.info(f"Ran test with {args}")
        """
        Namespace(cmd=<bound method Accounts_Commands._cmd_test of <poe_tracker.code.POE.accounts.accounts_commands.Accounts_Commands object at 0x7fac95c89990>>, league=None, message=<Message id=662204499120881674 channel=<TextChannel id=606974927308062750 name='bot_spam' position=2 nsfw=False news=False category_id=None> type=<MessageType.default: 0> author=<Member id=185846097284038656 name='Soton' discriminator='2585' bot=False nick='John' guild=<Guild id=346094316428591104 name='IsBe' shard_id=None chunked=True member_count=61>>>)
        """
        await args.message.channel.send(f"Trying to register a character {args.accounts}")
        for account in args.accounts:
            results = await self.api.get_characters(account)
            await args.message.channel.send(str(results), delete_after=10.0)
        

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
        """
        self.log.info("Check if character even exists")

        characters = []
        for char_name in args.names:
            if not await self.poe_sql.has_character_by_name(char_name):
                # await args.message.channel.send("Character not found.")
                # return
                continue

            char_dict = await self.poe_sql.get_character_dict_by_name(char_name)
            c = Character(char_dict, None)
            characters.append(c)
            self.log.info(f"Appended {c}")


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
            async for char in self.poe_sql.iter_characters():
                if not re.search(args.league, char['league'], flags=re.IGNORECASE):
                    continue
                char_dict = await self.poe_sql.get_character_dict_by_name(char['name'])
                c = Character(char_dict, None)
                if c not in characters:
                    characters.append(c)

        if not len(characters):
            await args.message.channel.send("I need chracters to plot!")
            return

        await Plotter(args).plot_character(characters, args.message.channel)