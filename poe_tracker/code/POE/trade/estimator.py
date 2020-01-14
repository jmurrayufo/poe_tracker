
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

    shard_correction = {
        "Mirror Shard": "Mirror of Kalandra",
        "Exalted Shard": "Exalted Orb",
        "Harbinger's Shard": "Harbinger's Orb",
        "Ancient Shard": "Ancient Orb",
        "Annulment Shard": "Orb of Annulment",
        "Binding Shard": "Orb of Binding",
        "Horizon Shard": "Orb of Horizons",
        "Engineer's Shard": "Engineer's Orb",
        "Chaos Shard": "Chaos Orb",
        "Alchemy Shard": "Orb of Alchemy",
        "Regal Shard": "Regal Orb",
        "Alteration Shard": "Orb of Alteration",
        "Transmutation Shard": "Orb of Transmutation",
        "Scroll Fragment": "Scroll of Wisdom",
    }


    def __init__(self, use_cache=True, league=None, m=2.0, percentile=20):
        self.use_cache = use_cache
        self.league = league
        self.m = m
        self.percentile = percentile
        self.db = mongo.Mongo().db
        self.log = Log()


    async def price_out(self, item, category, depth=0):
        """ Price out a given item, or list of items

            @param items Iteratble of typeLine items to price.
            
            @return Dict of values {typeLine:value}. Will return None for values 
            that were not found. 
        """

        if depth > 1:
            return None

        if item == "Chaos Orb":
            return 1

        # Check to see if we get a cache hit
        if self.use_cache:
            # Init value incase we don't set this later
            old_value = None
            cache_dict = await self._check_cache(item, category)
            if cache_dict and datetime.datetime.utcnow() - cache_dict['_updatedAt'] < datetime.timedelta(minutes=cache_dict['_cache_factor']):
                # self.log.info(f"Using cached value for {item}")
                # self.log.info(datetime.datetime.utcnow() - cache_dict['_updatedAt'] )
                return cache_dict['_value']
            elif cache_dict:
                # We will use this value to update the chach
                old_value = cache_dict['_value']

        # For many shards, people post stupid values for them. Just calculate 1/20th their value and return that.
        if item in self.shard_correction:
            value_dict = await self._check_price(self.shard_correction[item], "currency", depth=depth)
            if value_dict is None:
                self.log.error(f"Cannot find price for sharded item `{item}`")
                return None

            # Adjust price to 1/20th, and correct name so we can cache it
            value_dict['estimate'] /= 20
            # value_dict['_value_name'] = item
        else:
            # Grab current price
            value_dict = await self._check_price(item, category, depth=depth)

        # Check for None values
        if value_dict is None:
            self.log.error(f"Cannot find price for `{item}`")
            return None

        # Update cache     
        value = value_dict['estimate']
        if self.use_cache:
            await self._update_cache(item, category, value, old_value)
        return value


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
        # TODO we really need to check the league from the command and use it here...
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
                await self.db.items.price.cache.find_one_and_update(
                    {"typeLine": typeLine, "extended.category": category},
                    {"$mul": {"_cache_factor": 0.90}}
                )
            else:
                await self.db.items.price.cache.find_one_and_update(
                    {"typeLine": typeLine, "extended.category": category},
                    {"$mul": {"_cache_factor": 1.01}}
                )


    async def _check_price(self, typeLine, category, depth):

        values = []
        async for item_dict in self.db.items.find(
                {
                    "typeLine": typeLine,
                    "league":"Metamorph",
                    "_value_name": {"$exists": 1},
                    "extended.category": category,
                    "_value": {"$ne":None},
                    "_updatedAt": {"$gt": datetime.datetime.utcnow() - datetime.timedelta(hours=24)}
                }
        ):
            # Depending on what we got, we might need to nest lookups!
            if item_dict['_value_name'] == "Chaos Orb":
                values.append(item_dict['_value'])
            elif item_dict['_value_name'] == typeLine:
                continue
            else:
                val = await self.price_out(item_dict['_value_name'], "currency", depth=depth+1)
                if val is not None:
                    # Adjust the value by how many they want
                    val *= item_dict['_value']
                    values.append(val)
            await asyncio.sleep(0)

        # Find Inverse values as well
        if category == "currency":
            async for item_dict in self.db.items.find(
                    {
                        "typeLine": "Chaos Orb",
                        "league":"Metamorph",
                        "_value_name" : typeLine,
                        "_value": {"$exists":1},
                        "_value": {"$ne": 0},
                        "_updatedAt": {"$gt": datetime.datetime.utcnow() - datetime.timedelta(hours=24)}
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
        data['values'] = values
        return data
        

    def reject_outliers(self, data):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else 0.
        return data[s<self.m]
