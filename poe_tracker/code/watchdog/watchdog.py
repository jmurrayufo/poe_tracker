
import asyncio
import os
import sdnotify

from ..Log import Log

class Watchdog:

    def __init__(self):
        self.log = Log()

    async def loop(self):

        n = sdnotify.SystemdNotifier()
        n.notify("READY=1")
        self.log.info("Booted and ready to keep us alive")

        while 1:
            self.log.info("Sending notification")
            n.notify("WATCHDOG=1")
            await asyncio.sleep(60)