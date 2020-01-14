
# from ...args import Args
# from ...Log import Log
# from ...Log import Log
from . import item
from .. import mongo


class StashTab:


    def __init__(self, *, stash_dict=None, stash_id=None):
        self.db = mongo.Mongo().db
        self.stash_dict = stash_dict

        # We could get this from either location, prefer the dict
        if stash_dict is not None and 'id' in stash_dict:
            self.stash_id = self.stash_dict['id']
        else:
            self.stash_id = stash_id

    
    async def pull(self):
        """Pull current state from the mongoDB
        """
        if self.stash_id is None:
            raise ValueError("Cannot search for `None`")
        self.stash_dict = await self.db.stashes.find_one({"id":self.stash_id})


    async def items(self):
        """Iterate through items and return Item() objects for each
        """
        if self.stash_dict is None:
            await self.pull()

        for item_id in self.stash_dict['items']:
            i = item.Item(item_id=item_id)
            await i.pull()
            if i.item_dict is None:
                continue
            yield i


    async def count_item_stacks(self, typeLine, noteless=False):
        """Given a specific `typeLine`, return the total count in this stash

            If `noteless` is is set, only count items without a note set.
        """
        total = 0
        async for item in self.items():
            if item.item_dict['typeLine'] != typeLine:
                continue
            if noteless:
                if 'note' in item.item_dict:
                    continue
            total += len(item)
        return total



class StashTabSearch:
    """Find stash tabs with given criteria
    """


    def __init__(self):
        self.db = mongo.Mongo().db


    async def search(self, 
                          stash_id=None,
                          account_name=None,
                          league=None,
                          stash_tab_name=None,
                          limit=0
    ):
        _filter = {}
        if stash_id:
            _filter['id'] = stash_id
        if account_name:
            _filter['accountName'] = account_name
        if league:
            _filter['league'] = league
        if stash_tab_name:
            _filter['stash'] = stash_tab_name

        async for stash in self.db.stashes.find(_filter, limit=limit):
            yield StashTab(stash_dict=stash)

        
