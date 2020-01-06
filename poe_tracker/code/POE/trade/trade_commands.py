
from ...args import Args
from ...Log import Log
from .. import mongo
import datetime
from pymongo import ReturnDocument
import re
import numpy as np
from . import price


class TradeCommands:

    def __init__(self):
        self.log = Log()
        self.ready = False
        self.db = mongo.Mongo().db
        self.args = Args()

    async def test(self, args):
        # self.log.info(f"Ran test with {args}")
        await args.message.channel.send("Hello!")

        values = await self.db.items.currency.distinct("typeLine",filter={"typeLine":re.compile(args.currency,re.I)})
        if len(values) > 1:
            await args.message.channel.send(f"Found {len(values)} potential matches, care to trim?")
            await args.message.channel.send(f"{', '.join(values)}")
            return

        values = []
        async for item_dict in self.db.items.currency.find(
                {
                    "typeLine":re.compile(args.currency,re.I),
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
        await args.message.channel.send(f"Found {len(values):,d}") 
        await args.message.channel.send(f"Estimated at {est}")
        for v in values:
            await args.message.channel.send(f"{v}")
            break



        

