#!/usr/bin/env python3.7


from poe_tracker.code.POE import Character, Account
from pprint import pprint
import time

accounts = ['jmurrayufo','naxamous']

for account_name in accounts:
    print(f"Checking account: {account_name}")

    a = Account(accountName=account_name)
    a.get_characters()

    for i in a.data:
        print(i)