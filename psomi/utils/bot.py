from discord.ext.commands import Bot
from psomi.utils.data import Data

class PsomiBot(Bot):
    def __init__(self, db_path: str, *args, **kwargs):
        self.__database: Data = Data(db_path)

        super().__init__(*args, **kwargs)

    @property
    def database(self):
        return self.__database
