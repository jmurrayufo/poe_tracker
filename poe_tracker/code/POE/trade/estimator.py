
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


    async def price_out(self, item, category):
        """ Price out a given item, or list of items

            @param items Iteratble of typeLine items to price.
            
            @return Dict of values {typeLine:value}. Will return None for values 
            that were not found. 
        """
        if item == "Chaos Orb":
            return 1

        # Check to see if we get a cache hit
        if self.use_cache:
            old_value = None
            cache_dict = await self._check_cache(item, category)
            if cache_dict and datetime.datetime.utcnow() - cache_dict['_updatedAt'] < datetime.timedelta(minutes=cache_dict['_cache_factor']):
                # self.log.info(datetime.datetime.utcnow() - cache_dict['_updatedAt'] )
                return cache_dict['_value']
            elif cache_dict:
                old_value = cache_dict['_value']

        # Grab current price
        value_dict = await self._check_price(item, category)

        # Check for None values
        if value_dict is None:
            self.log.error(f"Cannot find price for {item}")
            return None

        # Update cache     
        value = value_dict['estimate']
        if self.use_cache:
            await self._update_cache(item, category, value, old_value)
        return value

    
    async def chaos_conversion(self, typeLine):
        """ Converts any valid currency to chaos

            @param typeLine Name of currency to convert

            @return Value of typeLine converted to chaos at current market rates
        """


    async def _check_cache(self, typeLine, category):
        cache_dict = await self.db.items.price.cache.find_one(
                {
                    "typeLine": typeLine,
                    "league": "Metamorph",
                    "extended.category": category
                }
        )
        return cache_dict


    async def _update_cache(self, typeLine, category, value, old_value):        
        await self.db.items.price.cache.find_one_and_update(
                {"typeLine": typeLine, "extended.category": category},
                {
                    "$setOnInsert":{
                        "typeLine": typeLine,
                        "extended.category": category,
                        "league": "Metamorph",
                        "_cache_factor": 5,
                    },
                    "$set":{
                        "_value": value,
                        "_updatedAt": datetime.datetime.utcnow(),
                    },
                },
                upsert=True,
        )
        # Update caching factors
        # If our value was close, grow by 1%
        # If our value is 5% or more off, shrink by 10%
        if old_value is not None:
            if abs(1-value/old_value) > 0.05:
                self.log.warning(f"Caught bad cache on {typeLine}, updateing value")
                await self.db.items.price.cache.find_one_and_update(
                    {"typeLine": typeLine, "extended.category": category},
                    {"$mul": {"_cache_factor": 0.90}}
                )
            else:
                await self.db.items.price.cache.find_one_and_update(
                    {"typeLine": typeLine, "extended.category": category},
                    {"$mul": {"_cache_factor": 1.01}}
                )




    async def _check_price(self, typeLine, category):
        values = []
        async for item_dict in self.db.items.find(
                {
                    "typeLine": typeLine,
                    "league":"Metamorph",
                    "_value_name" : "Chaos Orb",
                    "extended.category": category,
                    "_value": {"$ne":None},
                    "_updatedAt": {"$gt": datetime.datetime.utcnow() - datetime.timedelta(hours=6)}
                }
        ):
            values.append(item_dict['_value'])
            await asyncio.sleep(0)

        # Find Inverse values as well
        if 0 and category == "currency":
            async for item_dict in self.db.items.find(
                    {
                        "typeLine": "Chaos Orb",
                        "league":"Metamorph",
                        "_value_name" : typeLine,
                        "_value": {"$exists":1},
                        "_value": {"$ne": 0},
                        "_updatedAt": {"$gt": datetime.datetime.utcnow() - datetime.timedelta(hours=6)}
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
