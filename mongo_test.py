#!/usr/bin/env python

import pymongo

client = pymongo.MongoClient('mongodb://poe:poe@atlas.lan:27017/path_of_exile')
client = pymongo.MongoClient('atlas.lan:27017',
                      username='poe',
                      password='poe',
                      authSource='path_of_exile',
                      )
print(client)

db = client['path_of_exile']

config = db['config']
print(dir(config.find()))
print(config)

print(db)
for c in db.list_collections():
    print(c)
