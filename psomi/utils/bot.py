from cachetools import TTLCache
import random
import time
from discord.ext.commands import Bot
from psomi.utils.data import Data

class PsomiBot(Bot):
    def __init__(self, db_path: str, *args, **kwargs):
        self.__database: Data = Data(db_path)

        self.webhook_name = "omihook"
        self.user_cache = TTLCache(100, 60)

        self.__STRESS_TEST_INTERVAL = 60
        self.__last_stress_test = 0
        self.__last_stress_test_result = None

        super().__init__(*args, **kwargs)

    def preform_stress_test(self) -> dict[str, float | int]:
        """
        Perform a stress-test on the database.

        Returns the last result if the last test was preformed less than `__STRESS_TEST_INTERVAL` seconds ago.
        :return: A dict containing the test results.
        :rtype: dict[str, float | int]
        """
        if time.time()-self.__last_stress_test > self.__STRESS_TEST_INTERVAL:
            db = Data("database.db")
            users = db.get_all_user_ids()

            # Single user test.
            user_start = time.time()
            user = db.get_user(random.choice(users))
            for character in user.characters_flattened:
                db.get_character(user, character.name) # manually fetch each character again
            user_end = time.time()
            user_total = len(user.characters_flattened)

            # Database-wide test.
            mass_start = time.time()
            mass_total = 0

            for user in users:
                user = db.get_user(user)
                mass_total += len(user.characters_flattened)
                for character in user.characters_flattened:
                    db.get_character(user, character.name)
            mass_end = time.time()

            self.__last_stress_test = time.time()
            self.__last_stress_test_result = {
                "mass_time": round(mass_end-mass_start, 5),
                "mass_count": mass_total,
                "user_time": round(user_end-user_start, 5),
                "user_count": user_total,
                "last_test": self.__last_stress_test
            }

        return self.__last_stress_test_result

    @property
    def database(self):
        return self.__database
