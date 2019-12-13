import re
import shlex
import datetime
import asyncio

from ..Client import Client
from ..CommandProcessor import DiscordArgumentParser, ValidUserAction
from ..CommandProcessor.exceptions import NoValidCommands, HelpNeeded
from ..Log import Log
from ..SQL import SQL
from . import POE_SQL, POE_Loop, Account, Character

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
            prog=f"{self.client.user.display_name}",
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
            "--league","-l",
            help="Show current league only",
            action='store_true'
        )
        sub_parser.set_defaults(cmd=self._cmd_leaderboard)


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
        return


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

