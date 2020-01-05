#!/usr/bin/env python

import pymongo
import datetime

tz = datetime.timezone.utc
m = datetime.timedelta(minutes=1)

_filter = {
    'name': 'SotonPlantPotPewPew', 
    'experience': {'$lte': 1711199943}, 
    'date': {'$lt': datetime.datetime(2020, 1, 5, 3, 3, 30, 338980)}
}
_filter = {
    'name': 'SotonBuffUm', 
    'experience': {'$lte': 1792662841}, 
    'date': {'$lt': datetime.datetime(2020, 1, 5, 4, 40, 47, 719435)},
}
# tzinfo.utcoffset
client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

db = client.path_of_exile_dev
print(_filter)
print(datetime.datetime.utcnow())
datas = db.characters.xp.find(_filter,sort=[("date",-1)])
for data in datas:
    # data['date'] = data['date'].replace(tzinfo=tz)
    print(data)
    print(datetime.datetime.now() - data['date'])
    print(_filter['date']['$lt'] - data['date'])
    print(_filter['date']['$lt'])
    print(data['date'])
    print()

t2=datetime.datetime(2020, 1, 5,  4, 34, 16, 41767)
t1=datetime.datetime(2020, 1, 4, 21, 35, 15, 956000)

print(t2-t1)