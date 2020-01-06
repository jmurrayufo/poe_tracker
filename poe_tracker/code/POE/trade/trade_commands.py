
from . import price
from .. import mongo
from ...Log import Log
from ...args import Args
from fuzzywuzzy import fuzz 
from pymongo import ReturnDocument
import datetime
import numpy as np
import re

class TradeCommands:

    def __init__(self):
        self.log = Log()
        self.ready = False
        self.db = mongo.Mongo().db
        self.args = Args()

    async def test(self, args):
        # self.log.info(f"Ran test with {args}")
        await args.message.channel.send("Hello!")

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



        

