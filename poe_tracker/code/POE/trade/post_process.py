

class PostProcess:

    
    def __init__(self):
        pass


    async def process_stash(self, stash_dict):
        """Given a raw stash from the API, process it fully into the DB
        """


    async def process_item(self, item_dict, stash_id):
        """Given a raw item from the API, process it fully into the DB
        Returns:
            id of item
        """


    async def process_currency(self, item_dict):
        """Given some currency from the API, process it fully into the DB
        """
