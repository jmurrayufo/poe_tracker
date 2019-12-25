import pathlib
import sqlite3
import time
import re

from ...Log import Log

class Sql:

    def __init__(self, db_name):

        self.ready = False
        db_path = pathlib.Path(db_name)
        self.log = Log()
        if not db_path.is_file():
            self.create_db(db_name)

        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = self.dict_factory
        # self.client = Client()
        self.table_setup()
        self.log.info("SQL init completed")


    def create_db(self, db_name):
        self.log.warning("New DB file")
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        conn.commit()
        cur.execute("PRAGMA synchronous=1")
        conn.commit()
        conn.close()
        self.log.warning("Finished new DB file creation")


    @property
    def cur(self):
        return self.conn.cursor()


    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    
    def table_exists(self, table_name):
        cmd = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        if self.cur.execute(cmd).fetchone():
            return True
        return False


    def commit(self):
        # Schedule a commit in the future
        # Get loop from the client, schedule a call to _commit and return
        self.conn.commit()


    def table_setup(self):
        """Setup any SQL tables needed for this class
        """
        self.log.info("Check to see if stashes exists.")
        if not self.table_exists("currency"):
            self.log.info("Create stashes table")
            cur = self.cur
            cmd = """
                CREATE TABLE IF NOT EXISTS stashes
                (
                    timestamp INTEGER NOT NULL,
                    id TEXT NOT NULL UNIQUE,
                    account_name TEXT,
                    league TEXT NOT NULL,
                    name TEXT,
                    stash_type TEXT
                )"""
            cur.execute(cmd)
            # cmd = "CREATE INDEX IF NOT EXISTS stash_ids ON stashes (id)"
            # cur.execute(cmd)
            self.commit()
        self.log.info("Check to see if currency exists.")
        if not self.table_exists("currency"):
            self.log.info("Create currency table")
            cur = self.cur
            cmd = """
                CREATE TABLE IF NOT EXISTS currency
                (
                    timestamp INTEGER NOT NULL, --Time entry hit DB
                    stash_id TEXT NOT NULL,
                    type_line TEXT NOT NULL,
                    note TEXT NOT NULL,
                    value REAL,
                    value_name TEXT,
                    valid BOOLEAN DEFAULT 1,
                    FOREIGN KEY(stash_id) REFERENCES stashes(id)
                )"""
            cur.execute(cmd)
            self.commit()


    def upsert_stash(self, stash_dict):

        if stash_dict['league'] is None:
            self.log.error("Found a stash dict with no league? WTF?!")
            self.log.error(stash_dict)
            exit()

        cmd = r"""
        INSERT OR REPLACE INTO stashes (
            timestamp,
            id,
            account_name,
            league,
            name,
            stash_type
        ) VALUES (
            ?,?,?,?,?,?
        )
        """
        cur = self.cur
        cur.execute(cmd, 
            (
                int(time.time()),
                stash_dict['id'],
                stash_dict['accountName'],
                stash_dict['league'],
                stash_dict['stash'],
                stash_dict['stashType']
            )
        )
        self.commit()
        # self.log.info(f"Inserted STASH {stash_dict['id'][:5]}... {stash_dict['accountName']}->{stash_dict['stash']}")

    def upsert_item(self, item_dict, stash_dict):
        self.log.info(f"Inserted CURRENCY {item_dict['name']}{stash_dict['id'][:5]}... {stash_dict['accountName']}->{stash_dict['stash']}")

        # Parse out the notes field if we can
        self.log.info(f"Attemt to split {item_dict['note']}")
        match_obj = re.search(r"~(b\/o|price) *([\d\.\/,]+)? *([\w\- ']+)$", item_dict['note'])
        if match_obj:
            self.log.info(match_obj.groups())
            pass
        else:
            self.log.error("Parse failed")
            with open("errors.txt","a") as fp:
                fp.write(f"{item_dict['note']}\n")
            return

        try:
            value = eval(match_obj.group(2)) if match_obj.group(2) is not None else 1
        except (SyntaxError, ZeroDivisionError):
            self.log.exception("Eval errored out, catch and return")
            return

        if type(value) not in [float,int]:
            with open("errors.txt","a") as fp:
                fp.write(f"{item_dict['note']}\n")
            self.log.error("Failed to parse")
            return

        cmd = r"""
        INSERT OR REPLACE INTO currency ( 
            timestamp,
            stash_id,
            type_line,
            note,
            value,
            value_name
        ) VALUES (
            ?,?,?,?,?,?
        )
        """
        cur = self.cur
        cur.execute(cmd,
            (
                int(time.time()),
                stash_dict['id'],
                item_dict['typeLine'],
                item_dict['note'],
                value,
                match_obj.group(3)
            )
        )
        self.conn.commit()