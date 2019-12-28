



from ..Singleton import Singleton
from ..Log import Log

class Mongo(metaclass=Singleton):


    def __init__(self, db_name):

        self.ready = False
        self.log = Log()
        if not db_path.is_file():
            self.create_db(db_name)

        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = self.dict_factory
        self.client = Client()
        self._commit_in_progress = False
        self.log.info("SQL init completed")
