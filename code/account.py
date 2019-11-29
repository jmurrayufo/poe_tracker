# https://www.pathofexile.com/character-window/get-characters?accountName=jmurrayufo

import requests
from . import character

class Account:

    acct_url = "https://www.pathofexile.com/character-window/get-characters?accountName={}"

    def __init__(self, accountName):
        self.accountName = accountName
        self.data = None


    def get_characters(self):
        acct_url = self.acct_url.format(self.accountName)
        r = requests.get(acct_url)
        r.raise_for_status()
        self.data = r.json()


    def characters(self):
        if self.data == None:
            self.get_characters()

        for i in self.data:
            yield character.Character(
                accountName=self.accountName, 
                character=i['name'], 
                league=i['league'])

