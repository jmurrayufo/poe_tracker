
from .. import mongo
from ..objects import stash_tab
from ...args import Args
from ...Log import Log
import asyncio
import datetime
import numpy as np
import time


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


    def __init__(self, use_cache=True, league=None, m=2.0, percentile=15):
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
            return None, None

        if item == "Chaos Orb":
            return 1, 1

        # Check to see if we get a cache hit
        if self.use_cache:
            # Init value incase we don't set this later
            old_value = None
            cache_dict = await self._check_cache(item, category)
            if cache_dict and datetime.datetime.utcnow() - cache_dict['_updatedAt'] < datetime.timedelta(minutes=cache_dict['_cache_factor']):
                # self.log.info(f"Using cached value for {item}")
                # self.log.info(datetime.datetime.utcnow() - cache_dict['_updatedAt'] )
                return cache_dict['_value'], cache_dict['count']
            elif cache_dict:
                # We will use this value to update the chach
                old_value = cache_dict['_value']
                count = cache_dict['count']

        # For many shards, people post stupid values for them. Just calculate 1/20th their value and return that.
        if item in self.shard_correction:
            value_dict = await self._check_price(self.shard_correction[item], "currency", depth=depth)
            if value_dict is None:
                self.log.error(f"Cannot find price for sharded item `{item}`")
                return None, None

            # Adjust price to 1/20th, and correct name so we can cache it
            value_dict['estimate'] /= 20
            # value_dict['_value_name'] = item
        else:
            # Grab current price
            value_dict = await self._check_price(item, category, depth=depth)

        # Check for None values
        if value_dict is None:
            self.log.error(f"Cannot find price for `{item}`")
            return None, None


        count = value_dict['count']

        # Update cache     
        if self.use_cache:
            await self._update_cache(item, category, value_dict['estimate'], old_value, count)

        # Return the whole dict
        return value_dict['estimate'], value_dict['count']


    async def _check_cache(self, typeLine, category):
        cache_dict = await self.db.items.price.cache.find_one(
                {
                    "typeLine": typeLine,
                    "league": "Metamorph",
                    "extended.category": category
                }
        )
        return cache_dict


    async def _update_cache(self, typeLine, category, value, old_value, count):    
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
                        "count": count,
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

        # This will be a list of (value, count) elements, we will squash this later
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
            count = item_dict['stackSize'] if 'stackSize' in item_dict else 1

            # Depending on what we got, we might need to nest lookups!
            if item_dict['_value_name'] == "Chaos Orb":
                values.append( (item_dict['_value'], count) )
            elif item_dict['_value_name'] == typeLine:
                continue
            else:
                val, _ = await self.price_out(item_dict['_value_name'], "currency", depth=depth+1)
                if val is not None:
                    # Adjust the value by how many they want
                    val *= item_dict['_value']
                    values.append( (val, count) )
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
                # count = item_dict['stackSize'] if 'stackSize' in item_dict else 1
                values.append( (1/item_dict['_value'],1) )
                await asyncio.sleep(0)

        if len(values) == 0:
            return None
        values = np.asarray(values)

        values = self.reject_outliers(values)
        # print(values)

        data = {}
        data['mean'] = np.mean(values)
        data['median'] = np.median(values)
        data['stddev'] = np.std(values)
        data['min'] = np.amin(values)
        data['max'] = np.amax(values)
        # data['estimate'] = np.percentile(values[:,0], self.percentile)
        data['estimate'] = self.weighted_percentile(values[:,0], self.percentile, values[:,1])
        data['count'] = sum(values[:,1])
        return data
        

    def reject_outliers(self, data):
        d = np.abs(data[:,0] - np.median(data[:,0]))
        mdev = np.mean(d)
        s = d/mdev if mdev else 0.
        ret_val = data[s<self.m]
        if ret_val.ndim > 2:
            return ret_val[0]
        else:
            return ret_val

    @staticmethod
    def weighted_percentile(data, percents, weights=None):
        ''' percents in units of 1%
            weights specifies the frequency (count) of data.
        '''
        if weights is None:
            return np.percentile(data, percents)
        ind=np.argsort(data)
        d=data[ind]
        w=weights[ind]
        p=1.*w.cumsum()/w.sum()*100
        y=np.interp(percents, p, d)
        return y