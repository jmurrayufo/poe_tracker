
from contextlib import redirect_stdout
import argparse
import io
import re

from ..Log import Log
from .exceptions import NoValidCommands, HelpNeeded


class DiscordArgumentParser(argparse.ArgumentParser):

    def parse_args(self, *args, **kwargs):
        f = io.StringIO()
        try:
            with redirect_stdout(f):
                return super().parse_args(*args, **kwargs)
        except SystemExit:
            Log().info("Sys Exit Capture")
            return f.getvalue()

    # def exit(self, status=0, message=None):
    #     raise TypeError(message)
    #     return None

    def error(self, message):
        # Log().info(type(message))
        if message.startswith("invalid choice:"):
            # This isn't a valid command, just continue
            raise NoValidCommands(message)
        else:
            raise HelpNeeded(message)
        return


class ValidUserAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            setattr(namespace, self.dest, None)
            return

        try:
            value = re.search(r"<@(?:&|!)?(\d+)>", values).group(1)
            setattr(namespace, self.dest, value)
            if re.match("<@&", values):
                setattr(namespace, "user_type", "role")
            else:
                setattr(namespace, "user_type", "user")
        except:  # noqa: E722
            raise HelpNeeded(f"{values} doesn't look like a user mention (try --help)")
