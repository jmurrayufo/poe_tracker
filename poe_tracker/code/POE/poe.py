import asyncio
import datetime
import discord
import re
import shlex

from ..Client import Client
from ..CommandProcessor import DiscordArgumentParser, ValidUserAction
from ..CommandProcessor.exceptions import NoValidCommands, HelpNeeded
from ..Log import Log
from ..SQL import SQL
from . import POE_SQL, POE_Loop, Account, Character, Plotter

class POE:

    def __init__(self):
        self.client = Client()
        self.log = Log()
        self.ready = False
        self.sql = SQL()
        self.poe_sql = POE_SQL()


    async def on_message(self, message):
        if message.author == self.client.user:
            return

        if not self.ready:
            self.log.warning(f"Saw message before we were ready: {message.content}")
            return

        match_obj = re.match(r"^<@!?\d+>", message.content)
        if match_obj and len(message.mentions)>0 and message.mentions[0] == self.client.user:
            self.log.info("Saw a mention of me, handle it!")
            await self.command_proc(message)


    async def on_ready(self):
        asyncio.create_task(POE_Loop(120).loop())

        await self.poe_sql.table_setup()

        self.log.info("POE, ready to recieve commands!")
        self.ready = True


    async def command_proc(self, message):
        """Handle specific commands, or pass to the session_manager
        """
        self.log.info(f"{message.content}")
        cmd = re.sub(r"^<@!?\d+> ?","", message.content, count=1)
        self.log.info(f"Command was: '{cmd}'")

        parser = DiscordArgumentParser(
            description="Path of Exile Tracking Commands", 
            prog=f"@{self.client.user.display_name}",
            epilog=f"Example: @{self.client.user.display_name} register MyCoolAccountName")
        
        parser.set_defaults(message=message)
        sp = parser.add_subparsers()

        # Register new users
        sub_parser = sp.add_parser('register',
            description='Register a user account for tracking')
        sub_parser.add_argument(
            "accounts",
            help="user account",
            nargs='+',
        )
        sub_parser.set_defaults(cmd=self._cmd_register)

        # Display leaderboards for specific leagues
        sub_parser = sp.add_parser('leaderboard',
            description='Print out leaderboard')
        sub_parser.add_argument(
            "--character","-c",
            help="Show just a specific character",
            metavar="character_name",
            nargs=1,
        )
        sub_parser.add_argument(
            "--league", "-l",
            help="Show current league only",
            action='store_true'
        )
        sub_parser.set_defaults(cmd=self._cmd_leaderboard)

        # Test various things
        sub_parser = sp.add_parser('test',
            description='Debug command (please ignore)')
        sub_parser.add_argument(
            "name",
            help="Character name",
        )
        sub_parser.set_defaults(cmd=self._cmd_test)

        # List off characters
        sub_parser = sp.add_parser('list',
            description='List of characters')
        sub_parser.add_argument(
            "--league",
            help="Limit to a specific league",
            nargs=1,
        )
        sub_parser.add_argument(
            "--recent",
            action='store_true',
            help="Only give characters that have been updated recently",
        )
        sub_parser.add_argument(
            "--account",
            nargs=1,
            help="Only give characters under the given account",
        )
        sub_parser.set_defaults(cmd=self._cmd_list)

        try:
            self.log.info("Parse Arguments")
            results = parser.parse_args(shlex.split(message.content)[1:])
            # self.log.info(results)

            if type(results) == str:
                self.log.info("Got normal return, printing and returning")
                self.log.info(type(results))
                await message.channel.send(f"```{results}```")
                return

            elif hasattr(results, 'cmd'):
                # Looks like we got a valid command parsing, execute!
                await results.cmd(results)
                return

            else:
                msg = parser.format_help()
                await message.channel.send(msg)
                return
        except NoValidCommands as e:
            # We didn't get a subcommand, let someone else deal with this mess!
            self.log.error(e)
            self.log.error("???")
            pass
        except HelpNeeded as e:
            self.log.info("TypeError Return")
            self.log.info(e)
            msg = f"{e}. You can add `-h` or `--help` to any command to get help!"
            await message.channel.send(msg)
            return
        return








    async def _cmd_leaderboard(self, args):
        self.log.info("Print leaders!")

        top_per_account = {}
        async for char in self.poe_sql.iter_characters():
            char.update(await self.poe_sql.get_character_dict_by_name(char['name']))
            xp = await self.poe_sql.get_character_last_xp(Character(char, None))
            char.update(xp)

            if char['ac_name'] not in top_per_account:
                top_per_account[char['ac_name']] = char
                continue

            if top_per_account[char['ac_name']]['experience'] < char['experience']:
                top_per_account[char['ac_name']] = char

        message = "Top Characters:\n```\n"
        rank = 1
        for i in sorted(top_per_account, key=lambda x: top_per_account[x]['experience'], reverse=True):
            self.log.info(top_per_account[i])
            char = top_per_account[i]
            char_and_account = f"{char['name']} ({char['ac_name']})"
            message += f"{rank}) {char_and_account:>30} XP: {char['experience']:,} (Level:{char['level']}) \n"
            rank += 1
        message += "```"

        await args.message.channel.send(message)








    async def _cmd_register(self, args):

        for account in args.accounts:

            a = Account(account)
            if not a.check_good():
                await args.message.channel.send(f"Account `{account}` doesn't seem ot be valid?")
                continue

            success = await self.poe_sql.register_account(account)
            if success:
                self.log.info(f"Registered {account}")
                await args.message.channel.send(f"Registered {account}")
            else:
                self.log.warning(f"Cannot register {account}, account already exists.")
                await args.message.channel.send(f"Cannot register {account}, account already exists.")


    async def _cmd_test(self, args):
        self.log.info("Check if character even exists")

        if not await self.poe_sql.has_character_by_name(args.name):
            await args.message.channel.send("Character not found.")
            return

        char_dict = await self.poe_sql.get_character_dict_by_name(args.name)
        c = Character(char_dict, None)

        await Plotter().plot_character(c, args.message.channel)


    async def _cmd_list(self, args):
        """
        "--league LEAGUE",
        "--recent",
        "--account ACCOUNT",
        """
        # em = discord.Embed()
        message = "```\n"
        async for char in self.poe_sql.iter_characters():
            # self.log.info(char)
            # em.add_field(name=char['aname'], value=char['name'])
            message += f"{char['name']:20} ({char['ac_name']})\n"

        message += "```"
        await args.message.author.send(message)
        await args.message.channel.send("Lists are big, check your DMs.")
