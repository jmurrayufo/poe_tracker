#!/usr/bin/env python

import pymongo
import datetime
import sqlite3
import time
import pathlib

class SQL:
    """Manage SQL connection, as well as basic user information
    """


    def __init__(self, db_name):

        self.ready = False
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = self.dict_factory


    @property
    def cur(self):
        return self.conn.cursor()


    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

"""
CREATE TABLE accounts
                (
                    account_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    created_at  INTEGER NOT NULL,
                    last_active INTEGER
                );
CREATE TABLE characters
                (
                    character_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id      INTEGER NOT NULL,
                    name            TEXT    NOT NULL,
                    league          TEXT    NOT NULL,
                    class_id         INTEGER NOT NULL,
                    ascendancy_class INTEGER NOT NULL,
                    class           TEXT    NOT NULL,
                    created_at      INTEGER NOT NULL,
                    last_active     INTEGER,
                    FOREIGN KEY(account_id) REFERENCES accounts(account_id)
                );
CREATE TABLE experience
                (
                    character_id    INTEGER NOT NULL,
                    level           INTEGER NOT NULL,
                    experience      INTEGER NOT NULL,
                    timestamp       INTEGER NOT NULL,
                    UNIQUE(character_id, experience),
                    FOREIGN KEY(character_id) REFERENCES characters(character_id)
                );
"""

"""
ACCOUNTS
{
    "_id" : ObjectId("5e1179c6996dc5906613f092"),
    "accountName" : "jmurrayufo",
    "discordId" : 185846097284038656,
    "lastActive" : ISODate("2020-01-04T22:53:10.847-07:00"),
    "registrationDate" : ISODate("2020-01-04T22:53:10.847-07:00"),
    "stats" : {
        "total_experience" : 0,
        "lost_experience" : 0,
        "deaths" : 0,
        "playtime" : 362.099355,
        "lost_expereince" : 0,
        "total_experince" : 0
    }
}

CHARACTERS
{
    "_id" : ObjectId("5e1179c6996dc5906613f0a2"),
    "name" : "SotonBuffUm",
    "accountName" : "jmurrayufo",
    "ascendancyClass" : 3,
    "class" : "Guardian",
    "classId" : 5,
    "creationDate" : ISODate("2020-01-04T22:53:10.867-07:00"),
    "experience" : 1792747101,
    "lastActive" : ISODate("2020-01-04T22:53:56.162-07:00"),
    "league" : "Metamorph",
    "level" : 89,
    "stats" : {
        "total_experience" : 0,
        "lost_experience" : 0,
        "deaths" : 0,
        "playtime" : 45.295646,
        "lost_expereince" : 0,
        "total_experince" : 0
    }
},

XP
{
    "_id" : ObjectId("5e1179f4ed5cebbf3e2a24ba"),
    "name" : "SotonBuffUm",
    "experience" : 1792747101,
    "level" : 89,
    "date" : ISODate("2020-01-04T22:53:56.162-07:00"),
    "league" : "Metamorph"
},
"""

# tzinfo.utcoffset
client = pymongo.MongoClient('atlas.lan:27017', 
                    username='poe', 
                    password='poe', 
                    authSource='admin')

m_db = client.path_of_exile

s_db = SQL("poe.db")

cur = s_db.cur

cur.execute("SELECT * FROM accounts")

accounts_map = dict() # character_id -> accountName
character_map = dict()

for account in cur.fetchall():
    # print(account)
    for character in cur.execute(f"SELECT * FROM characters WHERE account_id={account['account_id']}").fetchall():
        # print("   "+str(character))
        accounts_map[character['character_id']] = account['name']
        character_map[character['character_id']] = character['name']
# exit()
for xp in cur.execute(f"SELECT * FROM experience").fetchall():
    experience = xp['experience']
    name = character_map[xp['character_id']]
    level = xp['level']
    date = datetime.datetime.fromtimestamp(
        xp['timestamp'],
        datetime.timezone(datetime.timedelta(hours=-7))
        )
    league = cur.execute(f"SELECT league FROM characters WHERE character_id={xp['character_id']}").fetchone()['league']

    m_db.characters.xp.find_one_and_update(
            {"name": name,"date":date},
            {"$setOnInsert":
                {
                    "name":name,
                    "experience": experience,
                    "level":level,
                    "date":date,
                    "league":league
                }
            },
            upsert=True,
    )


# experience
#                 (
#                     character_id    INTEGER NOT NULL,
#                     level           INTEGER NOT NULL,
#                     experience      INTEGER NOT NULL,
#                     timestamp       INTEGER NOT NULL,
#                     UNIQUE(character_id, experience),
#                     FOREIGN KEY(character_id) REFERENCES characters(character_id)
#                 );

# XP
# {
#     "_id" : ObjectId("5e1179f4ed5cebbf3e2a24ba"),
#     "name" : "SotonBuffUm",
#     "experience" : 1792747101,
#     "level" : 89,
#     "date" : ISODate("2020-01-04T22:53:56.162-07:00"),
#     "league" : "Metamorph"
# },

exit()
self.db.accounts.find_one_and_update(
            {"accountName":account_name},
            {   
                "$set": { 
                    "accountName":account_name,
                    "discordId":args.message.author.id,
                    "lastActive":datetime.datetime.utcnow() 
                },
                "$setOnInsert": { 
                    "registrationDate":datetime.datetime.utcnow(),
                    "stats": { 
                        "total_experience": 0,
                        "lost_experience": 0,
                        "deaths": 0,
                        "playtime": 0
                    },
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )