
import json

from ..Singleton import Singleton
from ..Log import Log


class Config(metaclass=Singleton):


    def __init__(self, config_file="config.json"):
        """Load a config file for access throughout application
        """
        with open(config_file, 'r') as fp:
            self.data = json.load(fp)


    def __getitem__(self, key):
        return self.data[key]