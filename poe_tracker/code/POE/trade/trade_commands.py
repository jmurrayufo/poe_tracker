
from . import price
from .. import mongo
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
        """account, tab_name
        """
        self.log.info(f"Ran test with {args}")
        await args.message.channel.send(f"Begining search for stash tab `{args.tab_name}`")
        stashes = []
        async for stash_dict in self.db.stashes.find(
                {
                    "league": "Metamorph",
                    "stash": args.tab_name,
                    "accountName": args.account,
                }
        ):
            stashes.append(stash_dict)
        delay_message = await args.message.channel.send(f"<@{args.message.author.id}>, this might take me a moment...")
        value = 0.0
        t1 = time.time()
        for stash_dict in stashes:
            for item_id in stash_dict['items']:
                item_dict = await self.db.items.find_one({"id":item_id})
                if item_dict is None:
                    continue
                if item_dict['typeLine'] == "Chaos Orb":
                    value += item_dict['stackSize']
                    data = {'estimate': 1}
                else:
                    data = await self._estimate(item_dict['typeLine'], percentile=20)
                    if data is None:
                        await args.message.channel.send(f"I cannot price out {item_dict['typeLine']}, not enough data...")
                        continue
                stackSize = item_dict.get('stackSize', 1)
                value += data['estimate'] * stackSize
                print(f"{item_dict['typeLine']:>30} {stackSize:5} {data['estimate']:6.2f} {stackSize*data['estimate']:8.2f}  {value:8.2f}")
        await delay_message.delete()
        await args.message.channel.send(f"Estimated total value of {value:,.0f}C")
        self.log.info(f"Took {time.time()-t1} to process a test command")

    async def currency(self, args):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        def reject_outliers(data, m = 2.):
            d = np.abs(data - np.median(data))
            mdev = np.median(d)
            s = d/mdev if mdev else 0.
            return data[s<m]

        # self.log.info(f"Ran test with {args}")
        # await args.message.channel.send("Hello!")

        args.currency = ' '.join(args.currency)

        values = await self.db.items.currency.distinct("typeLine")
        match_str = []
        for v in values:
            f = fuzz.ratio(v,args.currency)
            match_str.append((f,v))


        match_str = sorted(match_str, key=lambda x:x[0])[-1]
        await args.message.channel.send(f"Searching for {match_str[1]} ({match_str[0]})")

        values = []
        async for item_dict in self.db.items.currency.find(
                {
                    "typeLine":match_str[1],
                    "league":re.compile("meta",re.I),
                }
        ):
            p = price.Price(item_dict['note'])
            if p.parse() and p.value_name == 'chaos':
                values.append(p)
        
        values = [p.value for p in values]
        values = np.asarray(values)

        values = reject_outliers(values, m=2)

        mean = np.mean(values)
        median = np.median(values)
        stddev = np.std(values)
        est = np.percentile(values, 20)
        
        if est > 10:
            est = f"{est:,.0f}"
        elif est > 0.1:
            est = f"{est:.2f}"
        else:
            est = f"{est:.3f}"

        await args.message.channel.send(f"Found {len(values):,d}") 
        await args.message.channel.send(f"Estimated at {est}C with a stddev of {stddev:.3f}")

        if args.plot:

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


    async def _estimate(self, typeLine, m=2.0, percentile=20):
        values = []
        async for item_dict in self.db.items.currency.find(
                {
                    "typeLine": typeLine,
                    "league":"Metamorph",
                    "_value_name" : "Chaos Orb",
                    "_value": {"$ne":None},
                }
        ):
            values.append(item_dict['_value'])

        # Find Inverse values as well
        async for item_dict in self.db.items.currency.find(
                {
                    "typeLine": "Chaos Orb",
                    "league":"Metamorph",
                    "_value_name" : typeLine,
                    "_value": {"$exists":1},
                    "_value": {"$ne": 0}
                }
        ):
            # self.log.info(item_dict)
            # await asyncio.sleep(1)
            values.append(1/item_dict['_value'])

        if len(values) == 0:
            return None
        
        values = np.asarray(values)

        values = self.reject_outliers(values, m=m)

        data = {}
        data['mean'] = np.mean(values)
        data['median'] = np.median(values)
        data['stddev'] = np.std(values)
        data['min'] = np.amin(values)
        data['max'] = np.amax(values)
        data['estimate'] = np.percentile(values, percentile)
        data['count'] = len(values)
        return data
        

    @staticmethod
    def reject_outliers(data, m = 2.0):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else 0.
        return data[s<m]
