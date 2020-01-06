#!/usr/bin/env python

import os

from .code.Client import Client
from .code.Log import Log
from .code.SQL import SQL
from .code.POE import POE
from .code.args import Args
# from .code.Stats import Stats
from . import version_info

def main():

    args = Args()
    args.parse()

    log = Log(args)

    log.info(f"Started with {version_info}")

    log.info(args)

    x = Client()


    #############################
    # Register all modules here #
    #############################

    x.register(POE())

    #############################
    # Register all modules here #
    #############################

    try:
        if args.token:
            log.info("Using token from args")
            x.run(args.token)
        elif os.environ.get('CLIENT_TOKEN', None):
            log.info("Using token from ENV")
            x.run(os.environ['CLIENT_TOKEN'])
        else:
            log.critical("No token was given in the arguments or the ENV!")
            raise RuntimeError("No valid token given, cannot start bot!")
    finally:
        log.critical("Shutdown complete")