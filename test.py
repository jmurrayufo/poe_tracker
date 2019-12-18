#!/usr/bin/env python3.7


from code import Character, Account
from pprint import pprint
import time

a = Account(accountName="jmurrayufo")
a.get_characters()

for c in a.characters():
    print(c)
    continue
    if c.character == "Sotonis":
        break
exit()
print(c)
for i in c.iter_items():
    # print(i)
    i
