

from pprint import pprint


class ItemButler:


    def __init__(self):
        pass


    def __new__(cls, *data, **kwargs):
        i = ItemBase(*data)
        return i


class ItemBase:


    def __init__(self, *args, **kwards):
        self.data = args[0]
        print("===")
        # pprint(self.data)
        print(self.data['typeLine'])
        print(self.data['name'])
        print(self.data['inventoryId'])
        pass
