import sqlite3
import os.path
import uuid
from dataclasses import dataclass
from threading import Lock


@dataclass
class Character:
    """
    Character Dataclass.

    Stores various information on a specific Proxy/Character.
    """
    name: str
    prefix: str
    # Optional
    avatar: str | None = None


class ProxyGroup:
    """
    Storage class for ProxyGroups.

    Contains a list of one or more Proxies (Characters) in no particular order.
    """
    def __init__(self, name: str, characters: list[Character]):
        """
        Initializes the ProxyGroup.

        :param name: The name of the group.
        :type name: str
        :param characters: Any Character objects it should store.
        :type characters: list[Character]
        """
        self.__characters = characters
        self.__name = name

    @property
    def name(self):
        """
        :returns: The ProxyGroup's name.
        :rtype: str
        """
        return self.__name

    def get_character_by_name(self, name: str) -> Character:
        """
        Get a character by their name.

        :param name: The name of the character.
        :type name: str
        :returns: A Character class representing them.
        :rtype: Character
        :raises ValueError: If no such character exists.
        """
        for character in self.__characters:
            if character.name == name:
                return character

        raise ValueError(f"No such character '{name}'.")

    def __repr__(self):
        return f"ProxyGroup(\"{self.__name}\", {self.__characters})"

    def __iter__(self):
        """
        Iterator.

        :returns: All characters under this group.
        """
        for _ in self.__characters:
            yield _


@dataclass
class User:
    """
    User Dataclass.

    Stores various information on a specific Discord user.
    """
    uid: str
    proxy_groups: list[ProxyGroup]


class Data:
    """
    Main Database class.

    Allows for the storage and modification of various Proxies and ProxyGroups.
    """
    def __init__(self, data_path: str):
        """
        Initializes the Database.

        If the database does not exist, it will be created via `_prep`, with all required tables
        automatically being created.
        :param data_path: The location of the database.
        :type data_path: str
        """
        self.__data_path = data_path
        self._prep()

    def _prep(self):
        if not os.path.exists(self.__data_path):
            with sqlite3.connect(self.__data_path) as conn:
                cursor = conn.cursor()

                # Create DB User Table
                #
                # tid: Table ID. Used to make table values unique.
                # did: Discord ID. Refers to the UUID of the User.
                #
                cursor.execute("""
                CREATE TABLE users (
                    tid TEXT PRIMARY KEY,
                    did TEXT UNIQUE NOT NULL
                )
                """)
                # Store ProxyGroups in their own table.
                cursor.execute("""
                CREATE TABLE proxy_groups (
                    tid TEXT PRIMARY KEY,
                    user_tid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY (user_tid) REFERENCES users(tid)
                )
                """)
                # As well as Characters, cross-referencing all of them together.
                cursor.execute("""
                CREATE TABLE characters (
                    tid TEXT PRIMARY KEY,
                    proxygroup_tid TEXT DEFAULT NULL,
                    user_tid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    avatar TEXT,
                    FOREIGN KEY (proxygroup_tid) REFERENCES proxy_groups(tid)
                    FOREIGN KEY (user_tid) REFERENCES users(tid)
                )
                """)

    def get_user(self, uid: str) -> User:
        """
        Reconstructs a User's entire profile from the DB.

        Includes all Characters and ProxyGroups registered under the UID.

        :param uid: The user's Discord UUID.
        :type uid: str
        :returns: The fully reconstructed User class.
        :rtype: User

        :raises IndexError: if the UUID is not valid or no such user exists.
        :raises TypeError: if the `uid` variable is not of type `str`.
        """
        if not isinstance(uid, str):
            raise TypeError(f"Argument 'uid' must be of type 'str', not '{uid.__class__.__name__}'.")

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # find the user by their Discord UUID, then locate all characters and ProxyGroups that are
            # linked to the user via its TID.
            final = []
            try:
                user = cursor.execute("SELECT * FROM users WHERE did=?", (uid,)).fetchall()[0]
            except IndexError as e:
                raise ValueError(f"No such user of UUID '{uid}'!") from e
            proxygroups = cursor.execute("SELECT * FROM proxy_groups WHERE user_tid=?", (user["tid"],)).fetchall()
            for group in proxygroups:
                # all characters have a link to their proxygroups, so we can filter them by the TID
                characters = cursor.execute("SELECT * FROM characters WHERE proxygroup_tid=?",
                                            (group["tid"],)).fetchall()
                characters = [Character(_["name"], _["prefix"], _["avatar"]) for _ in characters]  # reconstruction

                final.append(ProxyGroup(group["name"], characters))

            # add all characters without a group into a new "Uncategorized" ProxyGroup
            ungrouped = cursor.execute("SELECT * FROM characters WHERE user_tid=? AND proxygroup_tid IS NULL",
                                       (user["tid"],)).fetchall()
            final.append(
                ProxyGroup(
                    "Uncategorized",
                    [Character(_["name"], _["prefix"], _["avatar"]) for _ in ungrouped]
                )
            )

            return User(user["did"], final)

    def get_character(self):
        ...

    def add_character(self):
        ...

    def update_character(self):
        ...

    def remove_character(self):
        ...
