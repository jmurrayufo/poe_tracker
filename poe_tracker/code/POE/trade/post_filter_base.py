
import asyncio
from ...Log import Log

class Post_Filter_Base:

    log = Log()

    def __init__(self, callers = None):
        if type(callers) not in [list,tuple,None]:
            raise TypeError(f"Got invalid type {type(callers)}")
        self.callers = callers


    async def __call__(self, item):
        self.item = item
        self.ret = None
        await self.pre_process()

        if self.callers:
            for caller in self.callers:
                await asyncio.sleep(0)
                try:
                    r = await caller(item)
                    await self.mid_process()
                except StopCalls:
                    raise
                if r is not None:
                    self.item = r

        await self.post_process()

        if self.ret:
            return self.ret
        return None


    async def pre_process(self):
        pass


    async def mid_process(self):
        pass


    async def post_process(self):
        pass



class StopCalls(Exception):
    pass
