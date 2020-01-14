

# from ...Log import Log
from .. import mongo

class Item:
    """Base of all items
    """

    def __init__(self, item_dict=None, item_id=None):
        self.db = mongo.Mongo().db
        self.item_dict = item_dict
        self.item_id = item_id


    def __str__(self):
        if self.item_dict is None:
            return super().__str__()
        return f"I<{self.item_dict['typeLine']}>"

    
    async def pull(self):
        """Pull current state from the mongoDB
        """
        if self.item_id is None:
            raise ValueError("Cannot search for `None`")
        self.item_dict = await self.db.items.find_one({"id":self.item_id})


    async def iter_items(self):
        """Iterate through items and return Item() objects for each
        """
        if self.item_dict is None:
            await self.pull()


    def __len__(self):
        """The majority of things don't stack
        """
        if self.item_dict is not None and "stackSize" in self.item_dict:
            return self.item_dict['stackSize']
        return 1


class Currency(Item):


    async def value(self):
        """Convery self to value in units of Chaos Orbs
        """
        pass