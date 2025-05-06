from cachetools import TTLCache
from discord.ext.commands import Bot
from psomi.utils.data import Data

class PsomiBot(Bot):
    def __init__(self, db_path: str, *args, **kwargs):
        self.__database: Data = Data(db_path)

        self.webhook_name = "omihook"
        self.user_cache = TTLCache(100, 60)

        super().__init__(*args, **kwargs)

    @property
    def database(self):
        return self.__database
