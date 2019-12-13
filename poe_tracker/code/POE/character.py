# https://www.pathofexile.com/character-window/get-items?character=SotonAshKetch&accountName=jmurrayufo
# https://www.pathofexile.com/character-window/get-items?character=PolarSindragosa&accountName=Naxamous
# https://www.pathofexile.com/character-window/get-items?accountName=jmurrayufo&realm=pc&character=SotonAshKetch

import requests
from pprint import pprint
from .item import ItemBase, ItemButler

class Character:

    char_url = "https://www.pathofexile.com/character-window/get-items?accountName={}&realm=pc&character={}"
    stash_url = "https://www.pathofexile.com/character-window/get-stash-items?accountName={}&realm=pc&league={}&tabs=0&tabIndex={}&public=false"

    def __init__(self, char_dict, account):
        # {'name': 'Sotonis', 'league': 'Standard', 'classId': 3, 'ascendancyClass': 2, 'class': 'Elementalist', 'level': 80, 'experience': 866729768, 'lastActive': True}
        self.name = char_dict['name']
        self.league = char_dict['league']
        self.classId = char_dict['classId']
        self.ascendancyClass = char_dict['ascendancyClass']
        self._class = char_dict['class']
        self.level = char_dict['level']
        self.experience = char_dict['experience']
        self.account = account


    def __str__(self):
        return f"Character({self.name})"


    def update_inventory(self):
        char_url = self.char_url.format(self.accountName, self.character)
        r = requests.get(char_url)
        r.raise_for_status()
        self.inventory = r.json()


    def iter_items(self):
        """Iterate through the items
        """
        if self.inventory == None:
            self.update_inventory()

        for item in self.inventory['items']:
             yield ItemButler(item)
        for item in self.inventory['items']:
            print()
            pprint(item)


    def get_stash_tab(self, index=0):
        """CURRENTLY BROKEN
        """
        return NotImplemented
        stash_url = self.stash_url.format(
            self.accountName, 
            self.league,
            index,
            )

        r = requests.get(stash_url)
        r.raise_for_status()
        return r.json()
