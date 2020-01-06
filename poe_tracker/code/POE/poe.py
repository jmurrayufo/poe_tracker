import asyncio
import datetime
import discord
import re
import shlex

from . import mongo
from ..args import Args
from ..Client import Client
from ..CommandProcessor import DiscordArgumentParser, ValidUserAction
from ..CommandProcessor.exceptions import NoValidCommands, HelpNeeded
from ..Log import Log
from .trade import trade_loop, cleanup_loop, trade_commands
from .accounts import accounts_loop, accounts_commands
from ..watchdog import watchdog

class POE:

    def __init__(self, args=None):
        self.client = Client()
        self.log = Log()
        self.ready = False
        self.mongo = mongo.Mongo()
        self.args = Args()
        self.accounts_commands = accounts_commands.Accounts_Commands()
        self.trade_commands = trade_commands.TradeCommands()


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
        # Create the POE loop to handle background activities

        self.log.info("Begin POE on_ready()")
        await self.mongo.setup()

        self.accounts_loop = accounts_loop.Accounts_Loop()
        asyncio.create_task(self.accounts_loop.loop())
        
        self.trade_loop = trade_loop.Trade_Loop(self.args)
        asyncio.create_task(self.trade_loop.loop())

        self.cleanup_loop = cleanup_loop.CleanupLoop()
        asyncio.create_task(self.cleanup_loop.loop())

        self.watchdog_loop = watchdog.Watchdog()
        asyncio.create_task(self.watchdog_loop.loop())

        self.log.info("POE, ready to recieve commands!")
        r = await self.client.change_presence(
                activity=discord.Activity(
                        id=0,
                        name="POE Trade API", 
                        type=discord.ActivityType.watching,
                )
        )
        self.log.info(r)
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

        # Test various things
        sub_parser = sp.add_parser('test',
            description='Debug command (please ignore)',
            help='Break shit')
        sub_parser.add_argument(
            "currency",
            help="Currency to price",
            nargs='+',
        )
        sub_parser.add_argument(
            "--plot",
            action='store_true',
            help="Provide usefull plots",
        )
        sub_parser.set_defaults(cmd=self.trade_commands.test)

        # Register new users
        sub_parser = sp.add_parser('register',
            description='Register a user account for tracking',
            help='Register your account for tracking')
        sub_parser.add_argument(
            "account",
            help="user account/character name",
        )
        sub_parser.set_defaults(cmd=self.accounts_commands.register)

        # Display leaderboards for specific leagues
        sub_parser = sp.add_parser('leaderboard',
            description='Print out leaderboard',
            help='Show leaders of accounts I track')
        sub_parser.add_argument(
            "--league", "-l",
            help="Filter leagues (regex)",
        )
        sub_parser.add_argument(
            "--account", "-a",
            help="Filter accuont (regex)",
        )
        sub_parser.add_argument(
            "--recent", "-r",
            help="Filter by recent activity",
            metavar='HOURS',
            type=float,
        )
        sub_parser.add_argument(
            "--top", "-t",
            help="Filter to a league",
            default=10,
            type=int,
        )
        sub_parser.set_defaults(cmd=self.accounts_commands.leaderboard)

        # List off characters
        sub_parser = sp.add_parser('list',
            description='List of characters')
        sub_parser.add_argument(
            "--league",
            help="Limit to a specific league",
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
        sub_parser.set_defaults(cmd=self.accounts_commands.list)

        # Plot Characters or Leagues
        sub_parser = sp.add_parser('plot',
            description="Plot various player xp gains",
            help="Plot character xp")
        sub_parser.add_argument(
            "names",
            help="Character name",
            nargs="*",
        )
        sub_parser.add_argument(
            "--differential","-d",
            action='store_true',
            help="Calculate xp over time"
        )
        sub_parser.add_argument(
            "--league", "-l",
            help="Filter to a league",
        )
        sub_parser.add_argument(
            "--recent", "-r",
            help="Restrict to recent N hours",
            nargs="?",
            type=float,
            metavar="N",
            const=24,
        )
        sub_parser.set_defaults(cmd=self.accounts_commands.plot)

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
            await message.channel.send(str(e))
            self.log.error(e)
        except HelpNeeded as e:
            self.log.info("TypeError Return")
            self.log.info(e)
            msg = f"{e}. You can add `-h` or `--help` to any command to get help!"
            await message.channel.send(msg)
            return
        return




    async def _cmd_test(self, args):
        self.log.info("Useless test command")
        await args.message.channel.send(args)


