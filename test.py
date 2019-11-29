#!/usr/bin/env python3.7


from code import Character, Account
from pprint import pprint
import time

a = Account(accountName="jmurrayufo")
a.get_characters()

for c in a.characters():
    if c.character == "SotonAshKetch":
        break

print(c)
i = 0
while 1:
    d = c.get_stash_tab(i)
    pprint(d)
    time.sleep(1)