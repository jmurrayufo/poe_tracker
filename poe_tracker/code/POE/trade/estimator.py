
from .. import mongo
from ...args import Args
from ...Log import Log
import asyncio
import datetime
import numpy as np


""" Estimate value of various currency items
"""
class Estimator:

    cross_lookup_currencies = [
        ''
    ]


    def __init__(self, use_cache=True, league=None, m=2.0, percentile=20):
        self.use_cache = use_cache
        self.league = league
        self.m = m
        self.percentile = percentile
        self.db = mongo.Mongo().db
        self.log = Log()


    async def price_out(self, item):
        """ Price out a given item, or list of items

            @param items Iteratble of typeLine items to price.
            
            @return Dict of values {typeLine:value}. Will return None for values 
            that were not found. 
        """
        if item == "Chaos Orb":
            return 1
        # Check to see if we get a cache hit
        cache_dict = await self._check_cache(item)
        if cache_dict and datetime.datetime.utcnow() - cache_dict['_updatedAt'] < datetime.timedelta(minutes=5):
            # self.log.info(datetime.datetime.utcnow() - cache_dict['_updatedAt'] )
            return cache_dict['_value']

        # Grab current price
        ret_val = await self._check_price(item)

        # Check for None values
        if ret_val is None:
            self.log.error(f"Cannot find price for {item}")
            return None

        # Update cache     
        ret_val = ret_val['estimate']
        await self._update_cache(item, ret_val)
        return ret_val


    
    async def chaos_conversion(self, typeLine):
        """ Converts any valid currency to chaos

            @param typeLine Name of currency to convert

            @return Value of typeLine converted to chaos at current market rates
        """


    async def _check_cache(self, typeLine):
        cache_dict = await self.db.items.currency.cache.find_one({"typeLine": typeLine})
        return cache_dict


    async def _update_cache(self, typeLine, value):
        await self.db.items.currency.cache.find_one_and_update(
                {"typeLine": typeLine},
                {
                    "$set":{
                        "_value": value,
                        "_updatedAt": datetime.datetime.utcnow(),
                    },
                    "$setOnInsert":{
                        "typeLine": typeLine,
                    }
                },
                upsert=True,
        )


    async def _check_price(self, typeLine):
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
            await asyncio.sleep(0)

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
            values.append(1/item_dict['_value'])
            await asyncio.sleep(0)

        if len(values) == 0:
            return None
        
        values = np.asarray(values)

        values = self.reject_outliers(values)

        data = {}
        data['mean'] = np.mean(values)
        data['median'] = np.median(values)
        data['stddev'] = np.std(values)
        data['min'] = np.amin(values)
        data['max'] = np.amax(values)
        data['estimate'] = np.percentile(values, self.percentile)
        data['count'] = len(values)
        return data
        

    def reject_outliers(self, data):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else 0.
        return data[s<self.m]
