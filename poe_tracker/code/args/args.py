
import argparse
import shlex

from ..Singleton import Singleton


class Args(metaclass=Singleton):

    def __init__(self):
        pass

    def parse(self, args=None):
        if args is not None and type(args) is str:
            args = shlex.split(args)
        parser = argparse.ArgumentParser(description='Poe Bot')

        parser.add_argument('--name',
                            default="POEBot",
                            help='Name of this bot')

        parser.add_argument('--env',
                            default="dev",
                            help='Name environment')

        parser.add_argument('--token',
                            help='Token to use to login')

        parser.add_argument('--log-level',
                            choices=['INFO', 'DEBUG'],
                            default='INFO',
                            help='Token to use to login')

        
        self.args = parser.parse_args(args)


    def __getattr__(self, attr):
        return getattr(self.args, attr)
