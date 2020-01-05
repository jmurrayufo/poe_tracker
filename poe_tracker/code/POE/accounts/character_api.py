# https://www.pathofexile.com/character-window/get-items?character=SotonAshKetch&accountName=jmurrayufo
# https://www.pathofexile.com/character-window/get-items?character=PolarSindragosa&accountName=Naxamous
# https://www.pathofexile.com/character-window/get-items?accountName=jmurrayufo&realm=pc&character=SotonAshKetch
# https://www.pathofexile.com/character-window/get-characters?accountName=jmurrayufo
# https://www.pathofexile.com/character-window/get-account-name-by-character?character=Soton


"""Singleton class designed to handle interactions with the POE character API
    - Get account
    - Get character
    - Get items
    - Prevent lockout with timers
"""
from ...args import Args
from ...Log import Log
from .. import mongo
from ...Singleton import Singleton
import time
import httpx
import asyncio

class Character_Api(metaclass=Singleton):
    get_acct_url = "https://www.pathofexile.com/character-window/get-characters"
    get_acct_by_char_url = "https://www.pathofexile.com/character-window/get-account-name-by-character"
    get_items_url = "https://www.pathofexile.com/character-window/get-items"


    def __init__(self):
        self.log = Log()
        self.ready = False
        self.args = Args()
        last_call = time.time()
        self.next_valid_call_at = time.time()
        self.lock = asyncio.Lock()


    async def get_characters(self, account):
        # Check for the account itself
        r = await self._get(self.get_acct_url, params={"accountName":account})
        if r.status_code == 200:
            return account, r.json()

        self.log.info(f"Got response of {r.status_code}, will try by name next")

        # Maybe they gave us a character name?
        account = await self.get_account_by_character(account)
        if account is None:
            return None, None

        r = await self._get(self.get_acct_url, params={"accountName":account})
        if r.status_code == 200:
            return account, r.json()
        self.log.error(f"Got response of {r.text}, give up")
        return None, None


    async def get_account_by_character(self, character):
        r = await self._get(self.get_acct_by_char_url, params={"character":character})
        if r.status_code != 200:
            self.log.error(f"Got response of {r.text}, done")
            return None
        return r.json()['accountName']


    async def get_items(self, account, character):
        r = await self._get(self.get_items_url, params={"character":character, "accountName":account})
        if r.status_code != 200:
            self.log.error(f"Got response of {r.text}, done")
            return None
        return r.json()


    async def _get(self, url, params=None):
        # We lock here to guarentee that each command waits properly for the last one to complete
        # If we didn't lock here several commands could bypass the timeout in a bunch.
        async with self.lock:
            await self.timeout_avoidance()
            self.log.debug(f"Calling with params {params}")
            r = await httpx.get(url, params=params)
            await self.prime_timeout_avoidance(r.headers)
            return r


    async def timeout_avoidance(self):
        """
        """
        sleep_needed = max(0, self.next_valid_call_at - time.time())
        # self.log.info(f"Sleep for {sleep_needed}")
        await asyncio.sleep(sleep_needed)


    async def prime_timeout_avoidance(self, headers):
        """
        Given a poe API header (eg: 60:60:60, 60 requests allowed in 60 seconds with a 60 second block if exceeded)
        And a state (eg: 1:60:0, 1 request in the last 60 seconds with a 0 second timeout currently in effect)
        Return current recomended sleep
        'X-Rate-Limit-Ip': '60:60:60,200:120:900',
        'X-Rate-Limit-Ip-State': '1:60:0,1:120:0',
        We need to allow for complex policies if given them, such as this list seperated one!
        """
        try:
            policies = headers['X-Rate-Limit-Ip']
            states = headers['X-Rate-Limit-Ip-State']
        except KeyError:
            self.log.exception("Headers didn't have expected values")
            self.log.info(headers)
            raise
        sleep_needed = 0

        policy_lists = []
        for policy in policies.split(","):
            # self.log.info(f"Saw policy {policy}")
            policy_lists.append([int(i) for i in policy.split(":")])

        state_lists = []
        for state in states.split(","):
            # self.log.info(f"Saw state {state}")
            state_lists.append([int(i) for i in state.split(":")])

        for index in range(len(policy_lists)):
            # self.log.info(f"Parse {policy_lists[index]} against {state_lists[index]}")
            sleep_time = ((state_lists[index][0]/policy_lists[index][0])**10)*state_lists[index][1]
            sleep_needed = max(sleep_time, sleep_needed)
            # self.log.info(f"Need {sleep_time}")

        self.next_valid_call_at = time.time() + sleep_needed
