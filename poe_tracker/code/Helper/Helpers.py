
import asyncio


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
