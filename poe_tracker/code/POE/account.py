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


    def check_good(self):
        """
        Attempt to pull account information, return if good status!
        """
        acct_url = self.acct_url.format(self.accountName)
        r = requests.get(acct_url)
        if r.status_code == 200:
            return True
        return False



    def iter_characters(self):
        if self.data == None:
            self.get_characters()

        for character in self.data:
            yield character
