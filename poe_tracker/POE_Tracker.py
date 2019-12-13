#!/usr/bin/env python

import os
import argparse

from .code.Client import Client
from .code.Log import Log
from .code.SQL import SQL
from .code.POE import POE
# from .code.Stats import Stats

parser = argparse.ArgumentParser(description='Basic Bot Demo')

parser.add_argument('--name',
                    default="StellarFlux",
                    help='Name of this bot')

parser.add_argument('--env',
                    default="DEV",
                    help='Name environment')

parser.add_argument('--token',
                    help='Token to use to login')

parser.add_argument('--log-level',
                    choices=['INFO', 'DEBUG'],
                    default='INFO',
                    help='Token to use to login')

args = parser.parse_args()

log = Log(args)

log.info(args)

x = Client()


#############################
# Register all modules here #
#############################

x.register(SQL("poe.db"))
x.register(POE())
# x.register(Stats())
# x.register(Game())

#############################
# Register all modules here #
#############################


if args.token:
    log.info("Using token from args")
    x.run(args.token)
elif os.environ.get('CLIENT_TOKEN', None):
    log.info("Using token from ENV")
    x.run(os.environ['CLIENT_TOKEN'])
else:
    log.critical("No token was given in the arguments or the ENV!")
    raise RuntimeError("No valid token given, cannot start bot!")
