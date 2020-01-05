
import asyncio
import os
import sdnotify

from ..Log import Log
from ..Singleton import Singleton

class Watchdog(metaclass=Singleton):

    def __init__(self):
        self.log = Log()
        self.n = sdnotify.SystemdNotifier()

    async def loop(self):

        
        self.n.notify("READY=1")
        self.log.info("Booted and ready to keep us alive")

        while 1:
            self.log.debug("Sending notification")
            self.n.notify("WATCHDOG=1")
            await asyncio.sleep(60)


    def long_boot(self, extra_minutes):
        self.log.debug(f"Requesting {extra_minutes*60e6:,.0f}us of boot time")
        self.n.notify(f"EXTEND_TIMEOUT_USEC={extra_minutes*60e6:.0f}")