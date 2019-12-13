import re
import shlex
import datetime

from ..Client import Client
from ..CommandProcessor import DiscordArgumentParser, ValidUserAction
from ..CommandProcessor.exceptions import NoValidCommands, HelpNeeded
from ..Log import Log
from ..SQL import SQL



class POE:

    def __init__(self):
        self.client = Client()
        self.log = Log()
        self.ready = False
        self.sql = SQL()


    async def on_message(self, message):
        if message.author == self.client.user:
            return

        if not self.ready:
            self.log.warning(f"Saw message before we were ready: {message.content}")
            return

        match_obj = re.match(r"^<@!\d+>", message.content)
        if match_obj and len(message.mentions)>0 and message.mentions[0] == self.client.user:
            self.log.info("Saw a mention of me, handle it!")
            await self.command_proc(message)


    async def on_ready(self):
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
            "account",
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
            self.log.info(results)

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
            pass

        return

    async def _cmd_leaderboard(self, args):
        return

    async def _cmd_register(self, args):
        # message = args.message
        self.log.info(f"Regsiter {args}")
        self.log.warning("I don't actually know how to register users yet... Sorry!")
        await args.message.channel.send("Sorry, I don't actually know how to register you yet...")
        return
        user_id = args.user_id if args.user_id else args.message.author.id

        cur = self.sql.cur

        cmd = """
            SELECT * FROM channels
        """
        channel_data = cur.execute(cmd).fetchall()
        # Rekey this data
        channel_lookup = {}
        for channel in channel_data:
            channel_lookup[channel['channel_id']] = channel

        cmd = f"""
            SELECT * FROM user_channel_stats WHERE user_id={user_id}
        """
        user_data = cur.execute(cmd).fetchall()

        msg = f"Stats for user: <@{user_id}>"
        msg += "\n```\n"
        for row in user_data:
            self.log.info(row)

            # Check if we need to dump this message early
            if len(msg) > 1900:
                msg += "\n```"

                self.log.info(f"Message len is: {len(msg)}")
                await args.message.channel.send(msg)
                msg = "```\n"

            msg += f"\nChannel: {channel_lookup[row['channel_id']]['name']}\n"
            msg += f"      Messages: {row['messages']:,d}\n"
            last_active = datetime.datetime.fromtimestamp(row['last_active']).replace(microsecond=0)
            last_active_delta = datetime.datetime.utcnow().replace(microsecond=0) - last_active
            msg += f"   Last Active: {last_active} ({last_active_delta} ago)\n"
        msg += "\n```"

        self.log.info(f"Message len is: {len(msg)}")

        await args.message.channel.send(msg)

        self.log.info("Finished stat command")
        return