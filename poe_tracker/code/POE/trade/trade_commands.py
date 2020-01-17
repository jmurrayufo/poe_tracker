
from . import price
from .estimator import Estimator
from .. import mongo
from ..objects import stash_tab
from ...args import Args
from ...Log import Log
from fuzzywuzzy import fuzz 
from pymongo import ReturnDocument
import asyncio
import datetime
import discord
import io
import numpy as np
import re
import time

class TradeCommands:

    def __init__(self):
        self.log = Log()
        self.ready = False
        self.db = mongo.Mongo().db
        self.args = Args()


    async def test(self, args):
        self.log.info("Init a tab")
        # stash = stash_tab.StashTab(args.stash_id)
        t0 = time.time()
        async for item in self.db.items.find(
                {
                    "_value":{"$exists":1, "$ne":[0,1]},
                    "_value_name":{"$ne":"Chaos Orb"},
                }, 
                sort=[("_updatedAt",-1)]
        ):
            if time.time() - t0 > 10:
                return
            typeLine = item['typeLine']
            value = item['_value']
            value_name = item['_value_name']
            p = price.Price(_value=value, _value_name=value_name)
            await args.message.channel.send(f"Found {typeLine} for {value} {value_name} ({await p.as_chaos()})")
            await asyncio.sleep(1)

    async def stash(self, args):
        """account, tab_name
        """

        e = Estimator(use_cache=True)

        self.log.info(f"Ran command with {args}")
        await args.message.channel.send(f"Begining search for stash tab `{args.tab_name}`")
        
        # Manage args.account
        if args.account is None:
            account = await self.db.accounts.find_one({"discordId":args.message.author.id})
            if account is None:
                await args.message.channel.send(f"I don't have an account for you. Maybe consider using the `register` command first?")
                return
            args.account = account['accountName']

        # Find stashes 
        self.log.info("Begin to look for stashes")
        stashes = []
        async for stash_dict in self.db.stashes.find(
                {
                    "league": "Metamorph",
                    "stash": args.tab_name,
                    "accountName": args.account,
                }
        ):
            stashes.append(stash_dict)
        if not len(stashes):
            await args.message.channel.send(f"<@{args.message.author.id}>, I didn't find any stashes named `{args.tab_name}`. Try again?")
            return
        # delay_message = await args.message.channel.send(f"<@{args.message.author.id}>, this might take me a moment...")
        self.log.info("Begin to look for items")
        total_value = 0.0
        rich_send = []
        t1 = time.time()
        for stash_dict in stashes:
            for item_id in stash_dict['items']:
                item_dict = await self.db.items.find_one({"id":item_id})
                if item_dict is None:
                    continue

                # LIMITED CATEGORIES FOR NOW
                if item_dict['extended']['category'] not in ['currency', 'cards']:
                    continue
                
                value, count = await e.price_out(item_dict['typeLine'], item_dict['extended']['category'])
                
                if value is None:
                    continue
                
                stackSize = item_dict.get('stackSize', 1)
                total_value += value * stackSize
                rich_send.append(f"{item_dict['typeLine']:>30} {stackSize:5} {value:6.2f} {stackSize*value:8.2f}  {total_value:8.2f}")

        if args.rich:
            self.log.info("Begin rich DM")
            message_buffer = f"```\n{'Item':>30} {'#':>5} {'Val':>6} {'StkVal':>8} {'Total Val':>8}\n"
            for r in rich_send:
                message_buffer += r + "\n"
                if len(message_buffer) >= 1900 or id(r) == id(rich_send[-1]):
                    message_buffer += "```"
                    await args.message.channel.send(message_buffer)
                    message_buffer = "```\n"
        await args.message.channel.send(f"Estimated total value in `{args.tab_name}` is currently {total_value:,.0f}C")

    async def currency(self, args):

        e = Estimator()

        args.currency = ' '.join(args.currency)

        # Lookup in cache with fuzzification. 
        values = await self.db.items.price.cache.distinct("typeLine", {"extended.category":"currency"})
        match_str = []
        for v in values:
            f = fuzz.ratio(v,args.currency)
            match_str.append((f,v))
        match_str = sorted(match_str, key=lambda x:x[0])[-1]
        await args.message.channel.send(f"Searching for {match_str[1]} ({match_str[0]})")

        value, count = await e.price_out(match_str[1], "currency")

        await args.message.channel.send(f"Estimated at {value:,.2f}C ({count:,.0f})")

        if args.plot:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.hist(values, bins=100)
            # plt.grid()

            # Save figure to ram for printing to discord
            self.log.info("Write plots to buffer")
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight',dpi=100)
            
            plt.clf()
            plt.cla()
            plt.close()

            buf.seek(0)
            f = discord.File(buf, filename="chart.png")

            # Send message to discord
            self.log.info("Send to discord")
            await args.message.channel.send(file=f)
