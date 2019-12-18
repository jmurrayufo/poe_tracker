
import re
import shlex
import datetime

from ..Client import Client
from ..CommandProcessor import DiscordArgumentParser, ValidUserAction
from ..CommandProcessor.exceptions import NoValidCommands, HelpNeeded
from ..Log import Log
from ..SQL import SQL



class Stats:

    def __init__(self):
        self.client = Client()
        self.log = Log()
        self.ready = False
        self.sql = SQL()


    async def on_message(self, message):
        if not self.ready:
            self.log.warning(f"Saw message before we were ready: {message.content}")
            return

        self.log.debug(f"Saw message: {message.content}")

        match_obj = re.match("^>stat(s)?", message.content)
        if match_obj:
            self.log.info("Saw a command, handle it!")
            await self.command_proc(message)


    async def on_ready(self):
        self.log.info("Stats, ready to recieve commands!")
        self.ready = True


    async def command_proc(self, message):
        """Handle specific commands, or pass to the session_manager
        """
        parser = DiscordArgumentParser(description="A Test Command", prog=">stats")
        parser.set_defaults(message=message)
        sp = parser.add_subparsers()

        sub_parser = sp.add_parser('user',
                                   description='test something')
        sub_parser.add_argument(
            "user_id",
            action=ValidUserAction,
            help="Mention of the user in question",
            metavar="@user",
            nargs="?",
        )
        sub_parser.set_defaults(cmd=self._cmd_user)

        sub_parser = sp.add_parser('global',
                                   description='test something')
        sub_parser.set_defaults(cmd=self._cmd_global)

        try:
            self.log.info("Parse Arguments")
            results = parser.parse_args(shlex.split(message.content)[1:])
            self.log.info(results)
            if type(results) == str:
                self.log.info("Got normal return, printing and returning")
                self.log.info(type(results))
                await message.channel.send(results)
                return
            elif hasattr(results, 'cmd'):
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

    async def _cmd_user(self, args):
        # message = args.message

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

    async def _cmd_global(self, args):
        # message = args.message

        user_id = args.user_id if hasattr(args, "user_id") else args.message.author.id

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
            SELECT *
            FROM user_channel_stats
            LEFT JOIN users ON
                user_channel_stats.user_id = users.user_id
        """
        user_stats = cur.execute(cmd).fetchall()


        users = {}
        for row in user_stats:
            user_id = row['user_id']
            if user_id not in users:
                users[user_id] = {}
                users[user_id]['user_id'] = user_id
                users[user_id]['messages'] = 0
                users[user_id]['name'] = row['name']
                users[user_id]['display_name'] = row['display_name']
                users[user_id]['first_seen'] = datetime.datetime.fromtimestamp(row['first_seen']).replace(microsecond=0)
                users[user_id]['membership_days'] = (datetime.datetime.utcnow().replace(microsecond=0) - users[user_id]['first_seen']).total_seconds()
                users[user_id]['membership_days'] /= 60 * 60 * 24
            users[user_id]['messages'] += row['messages']

        users = [users[x] for x in users]

        users = sorted(users, reverse=True, key=lambda x: x['messages'] / x['membership_days'])

        msg = f"Global User Stats"
        msg += "\n```\n"
        rank = 1
        for user in users:
            # Check if we need to dump this message early
            if len(msg) > 1900:
                msg += "\n```"
                self.log.info(f"Message len is: {len(msg)}")
                await args.message.channel.send(msg)
                msg = "```\n"

            msg += f"\n{rank}) User: {user['display_name']}  Msg/Day: {user['messages']/user['membership_days']:,.0f}"
            rank += 1
        msg += "\n```"

        self.log.info(f"Message len is: {len(msg)}")
        await args.message.channel.send(msg)

        self.log.info("Finished stat command")
        return
