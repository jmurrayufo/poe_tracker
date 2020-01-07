
from . import price
from .. import mongo
from ...Log import Log
from ...args import Args
from fuzzywuzzy import fuzz 
from pymongo import ReturnDocument
import datetime
import numpy as np
import re
import io
import discord

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
            await args.message.channel.send(f"Found one!")
            stashes.append(stash_dict)
        await args.message.channel.send(f"Found them all, will now prase items.")
        value = 0.0
        for stash_dict in stashes:
            for item_id in stash_dict['items']:
                item_dict = await self.db.items.find_one({"id":item_id})
                if item_dict is None:
                    continue
                if item_dict['typeLine'] == "Chaos Orb":
                    value += item_dict['stackSize']
                    continue
                data = await self._estimate(item_dict['typeLine'])
                value += data['estimate'] * item_dict['stackSize']
                print(f"{item_dict['typeLine']:>30} {item_dict['stackSize']:5} {data['estimate']:6.2f} {item_dict['stackSize']*data['estimate']:8.2f}  {value:8.2f}")
        await args.message.channel.send(f"Estimated total value of {value:,.0f}C")


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
                    "typeLine":typeLine,
                    "league":"Metamorph",
                    "_value_name" : "chaos",
                    "_value": {"$ne":None},
                }
        ):
            values.append(item_dict['_value'])

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
        return data
        

    @staticmethod
    def reject_outliers(data, m = 2.0):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else 0.
        return data[s<m]
