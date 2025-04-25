import inspect
import sqlite3
import os.path
import uuid
from dataclasses import dataclass
from psomi.utils.checking import enforce_annotations

#TODO: Possibly find a better solution than tossing objects around?

@dataclass
class Character:
    """
    Character Dataclass.

    Stores various information on a specific Proxy/Character.
    """
    name: str
    prefix: str
    # Optional
    proxygroup_name: str | None = None
    avatar: str | None = None


class ProxyGroup:
    """
    Storage class for ProxyGroups.

    Contains a list of one or more Proxies (Characters) in no particular order.

    Note, that all ProxyGroup objects should be treated as read-only, with changes being made directly to the DB.
    """
    @enforce_annotations
    def __init__(self, name: str, tid: str | None, characters: list[Character]):
        """
        Initializes the ProxyGroup.

        :param name: The name of the group.
        :type name: str
        :param characters: Any Character objects it should store.
        :type characters: list[Character]
        """
        self.__characters = characters
        self.__name = name
        self.__tid = tid

    @property
    def name(self):
        """
        :returns: The ProxyGroup's name.
        :rtype: str
        """
        return self.__name

    @property
    def tid(self):
        """
        :return: The ProxyGroup's TID.
        :rtype: str
        """
        return self.__tid

    @property
    def characters(self):
        """
        :return: All Characters in this ProxyGroup.
        :rtype: list[Character]
        """
        return self.__characters

    @enforce_annotations
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
        return (f"ProxyGroup(\"{self.__name}\", " +
                ("None" if self.__tid is None else f"\"{self.__tid}\"")
                + f", {self.__characters})")

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
    tid: str
    proxy_groups: list[ProxyGroup]


def db_get_user_row(cursor: sqlite3.Cursor, did: str):
    try:
        return cursor.execute(
            "SELECT * FROM users WHERE did=?",
            (did,)
        ).fetchall()[0]
    except IndexError as e:
        raise ValueError(f"No such user of UUID '{did}'.") from e


def db_get_group_row(cursor: sqlite3.Cursor, user_tid: str, group_name: str):
    try:
        return cursor.execute(
            "SELECT * FROM proxy_groups WHERE user_tid=? AND name=?",
            (user_tid, group_name)
        ).fetchall()[0]
    except IndexError as e:
        raise ValueError(f"No such ProxyGroup of name '{group_name}'.") from e

def sort_by_page(groups: list, page_num: int, page_size: int) -> dict:
    """
    Sort a list of lists (groups) by pages, ensuring only one group is shown at a time.

    :param groups: The groups to sort.
    :type groups: list
    :param page_num: What page to fetch.
    :type page_num: int
    :param page_size: How large the page should be.
    :type page_size: int
    :return: The sorted page.
    :rtype: dict
    """
    for i, group in enumerate(groups):
        num_pages_in_group = -(-len(group) // page_size)

        if page_num <= num_pages_in_group:
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size
            return {
                "group_num": i+1,
                "page": group[start_idx:end_idx]
            }

        page_num -= num_pages_in_group  # Move to the next group

    return {"group_num": 0, "page": []}  # Return blank dict indicating out of bounds

def db_get_character(cursor: sqlite3.Cursor, user_tid: str, character_name: str):
    try:
        return cursor.execute(
            "SELECT * FROM characters WHERE user_tid=? AND name=?",
            (user_tid, character_name)
        ).fetchall()[0]
    except IndexError as e:
        raise ValueError(f"No such character with name '{character_name}'.") from e


class Data:
    """
    Main Database class.

    Allows for the storage and modification of various Proxies and ProxyGroups.
    """
    @enforce_annotations
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
                    FOREIGN KEY (proxygroup_tid) REFERENCES proxy_groups(tid) ON DELETE SET NULL,
                    FOREIGN KEY (user_tid) REFERENCES users(tid)
                    UNIQUE (user_tid, name)
                    UNIQUE (user_tid, prefix)
                )
                """)

    @enforce_annotations
    def get_user(self, uid: str) -> User:
        """
        Reconstructs a User's entire profile from the DB.

        Includes all Characters and ProxyGroups registered under the UID.

        :param uid: The user's Discord UUID.
        :type uid: str
        :returns: The fully reconstructed User class.
        :rtype: User

        :raises IndexError: if the UUID is not valid or no such user exists.
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # find the user by their Discord UUID, then locate all characters and ProxyGroups that are
            # linked to the user via its TID.
            final = []
            db_user = db_get_user_row(cursor, uid)
            db_proxygroups = cursor.execute(
                "SELECT * FROM proxy_groups WHERE user_tid=?",
                (db_user["tid"],)
            ).fetchall()
            for group in db_proxygroups:
                # all characters have a link to their proxygroups, so we can filter them by the TID
                db_characters = cursor.execute("SELECT * FROM characters WHERE proxygroup_tid=?",
                                            (group["tid"],)).fetchall()
                db_characters = [
                    Character(_["name"], _["prefix"], group["tid"], _["avatar"]) for _ in db_characters
                ]  # reconstruction

                final.append(ProxyGroup(group["name"], group["name"], db_characters))

            # add all characters without a group into a new "Uncategorized" ProxyGroup
            db_ungrouped = cursor.execute(
                "SELECT * FROM characters WHERE user_tid=? AND proxygroup_tid IS NULL",
                (db_user["tid"],)
            ).fetchall()

            final.append(
                ProxyGroup(
                    "Uncategorized",
                    None,
                    [Character(_["name"], _["prefix"], None, _["avatar"]) for _ in db_ungrouped]
                )
            )

            return User(db_user["did"], db_user["tid"], final)

    @enforce_annotations
    def add_user(self, uid: str) -> User:
        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                user_tid = str(uuid.uuid4())  # Generate a new UUID for the user
                cursor.execute(
                    "INSERT INTO users (tid, did) VALUES (?, ?)",
                    (user_tid, uid)
                )
            except sqlite3.IntegrityError as e:
                raise ValueError(f"User of UUID '{uid}' already exists in database!") from e

            return User(uid, user_tid, [])

    @enforce_annotations
    def get_proxygroup(self, user: User, name: str) -> ProxyGroup:
        """
        Find and reconstruct a User's ProxyGroup by its name.

        All ProxyGroup related methods will inherently trust the underlying database over objects supplied
        to them by arguments, so it is strongly recommended all ProxyGroup actions start here, where the data
        will be most accurate.

        :param user: The user to search for.
        :type user: User
        :param name: The name of the ProxyGroup to reconstruct.
        :type name: str
        :return: The reconstructed ProxyGroup.
        :rtype: ProxyGroup
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            db_user = db_get_user_row(cursor, user.uid)
            db_group = db_get_group_row(cursor, db_user["tid"], name)

            db_characters = cursor.execute(
                "SELECT * FROM characters WHERE proxygroup_tid=?",
                (db_group["tid"],)
            ).fetchall()

            return ProxyGroup(
                name,
                db_group["tid"],
                [Character(_["name"], _["prefix"], db_group["name"], _["avatar"]) for _ in db_characters]
            )

            # print(user)
            # print(group)
            # print(characters)

    @enforce_annotations
    def rename_proxygroup(self, user: User, proxy_group: ProxyGroup, new_name: str) -> ProxyGroup:
        """
        Modify a User's ProxyGroup name, then return a new ProxyGroup object.

        :param user: The User to search for.
        :type user: str
        :param proxy_group: The ProxyGroup to rename.
        :type proxy_group: ProxyGroup
        :param new_name: The ProxyGroup's new name.
        :type new_name: str
        :return: The renamed ProxyGroup.
        :rtype: ProxyGroup
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            db_user = db_get_user_row(cursor, user.uid)
            db_group = db_get_group_row(cursor, db_user["tid"], proxy_group.name)

            cursor.execute(
                "UPDATE proxy_groups SET name=? WHERE tid=?",
                (new_name,db_group["tid"])
            )

        return ProxyGroup(new_name, db_group["tid"], proxy_group.characters)

    @enforce_annotations
    def create_proxygroup(self, user: User, name: str) -> ProxyGroup:
        """
        Create a new ProxyGroup under a specific User, then return it.

        Characters must be added to this group later.

        :param user: The User to create the ProxyGroup for.
        :type user: User
        :param name: The name of the new ProxyGroup.
        :type name: str
        :return: The created ProxyGroup (read-only).
        :rtype: ProxyGroup
        """
        if name in [_.name for _ in user.proxy_groups]:
            raise ValueError(f"Duplicate entry ('{name}') for user of UUID '{user.uid}'.")

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            proxygroup_tid = str(uuid.uuid4())  # Generate a UUID for the proxy group
            cursor.execute(
                "INSERT INTO proxy_groups (tid, user_tid, name) VALUES (?, ?, ?)",
                (proxygroup_tid, user.tid, name)
            )

        return ProxyGroup(name, proxygroup_tid, [])

    @enforce_annotations
    def delete_proxygroup(self, user: User, proxy_group: ProxyGroup) -> None:
        """
        Delete a User's ProxyGroup by its name.

        Automatically unassigns any user within the group to Uncategorized.

        :param user: The User to search for.
        :type user: User
        :param proxy_group: The ProxyGroup to delete.
        :type proxy_group: ProxyGroup
        :return:
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            conn.execute("PRAGMA foreign_keys = ON") # disabled by default, so re-enable it for auto nullification
            db_user = db_get_user_row(cursor, user.uid)
            db_group = db_get_group_row(cursor, db_user["tid"], proxy_group.name)

            cursor.execute(
                "DELETE FROM proxy_groups WHERE tid=?",
                (db_group["tid"],)
            )

    @enforce_annotations
    def get_uncategorized(self, user: User) -> ProxyGroup:
        """
        Find and reconstruct a User's uncategorized characters (ones that do not belong to a ProxyGroup).

        Creates a pseudo-ProxyGroup to contain the characters under the name "Uncategorized".

        :param user: The User to search for.
        :type user: User
        :return: A ProxyGroup containing all Uncategorized characters.
        :rtype: ProxyGroup
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            db_user = db_get_user_row(cursor, user.uid)

            db_characters = cursor.execute(
                "SELECT * FROM characters WHERE user_tid=? AND proxygroup_tid IS NULL",
                (db_user["tid"],)
            ).fetchall()

            return ProxyGroup(
                "Uncategorized",
                None,
                [Character(_["name"], _["prefix"], None, _["avatar"]) for _ in db_characters]
            )

    @enforce_annotations
    def get_character(self, user: User, name: str) -> Character:
        """
        Find and reconstruct a User's Character by their name.

        :param user: The User to search for.
        :param name: The Character's name.
        :return: The reconstructed Character.
        :rtype: Character
        """

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            db_user = db_get_user_row(cursor, user.uid)

            try:
                db_character = db_get_character(cursor, db_user["tid"], name)
                character_group = cursor.execute(
                    "SELECT name FROM proxy_groups WHERE tid=?",
                    (db_character["proxygroup_tid"],)
                ).fetchone()[0]
            except TypeError: # fetchone returns None instead of a single item list if it can't find something.
                character_group = None

            return Character(
                db_character["name"],
                db_character["prefix"],
                character_group,
                db_character["avatar"]
            )

    @enforce_annotations
    def create_character(self, user: User, name: str, prefix: str, avatar: str | None) -> Character:
        """
        Create a new Character under a specific user, then return it.

        Note, that all new Characters are Uncategorized.

        :param user: The User to search for.
        :type user: User
        :param name: The Character's name.
        :type name: str
        :param prefix: The Character's prefix.
        :type prefix: str
        :param avatar: The Character's avatar URL, if any.
        :type avatar: str | None
        :return: The created Character.
        :rtype: Character
        """
        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            db_user = db_get_user_row(cursor, user.uid)
            # note: characters are uncategorized by default
            try:
                character_tid = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO characters (tid, proxygroup_tid, user_tid, name, prefix, avatar) VALUES "
                    "(?, ?, ?, ?, ?, ?)",
                    (character_tid, None, db_user["tid"], name, prefix, avatar)
                )
            except sqlite3.IntegrityError as e:
                raise ValueError(f"One or more values failed database integrity checks!")

        return Character(name, prefix, None, avatar)

    @enforce_annotations
    def delete_character(self, user: User, character: Character):
        """
        Delete a User's Character.

        :param user: The User to search for.
        :type user: User
        :param character: The Character to delete.
        :type character: Character
        :return:
        """
        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            db_user = db_get_user_row(cursor, user.uid)
            db_character = db_get_character(cursor, db_user["tid"], character.name)
            cursor.execute(
                "DELETE FROM characters WHERE tid=?",
                (db_character["tid"],)
            )

    @enforce_annotations
    def group_character(self, user: User, character: Character, proxy_group: ProxyGroup) -> Character:
        """
        Add a User's Character into a ProxyGroup, then return the updated Character object.

        :param user: The User to search for.
        :type user: User
        :param character: The Character to add to the ProxyGroup.
        :type character: Character
        :param proxy_group: The ProxyGroup to add them to.
        :type proxy_group: ProxyGroup
        :return: The updated Character.
        :rtype: Character
        """
        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            db_user = db_get_user_row(cursor, user.uid)
            db_group = db_get_group_row(cursor, db_user["tid"], proxy_group.name)
            db_character = db_get_character(cursor, db_user["tid"], character.name)

            if db_character["proxygroup_tid"] == db_group["tid"]:
                raise ValueError(f"Character '{character.name}' is already present in ProxyGroup '{proxy_group.name}'")

            cursor.execute(
                "UPDATE characters SET proxygroup_tid=? WHERE tid=?",
                (db_group["tid"], db_character["tid"])
            )

            return Character(
                character.name,
                character.prefix,
                db_group["name"],
                character.avatar
            )


    def ungroup_character(self, user: User, character: Character) -> Character:
        """
        Remove a User's Character from whatever ProxyGroup they belong to, then return it.

        :param user: The User to search for.
        :param character: The Character to remove from the ProxyGroup.
        :return: The updated Character.
        :rtype: Character
        """
        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            db_user = db_get_user_row(cursor, user.uid)
            db_character = db_get_character(cursor, db_user["tid"], character.name)

            if db_character["proxygroup_tid"] is None:
                raise ValueError(f"Character '{character.name}' does not belong to a ProxyGroup!")

            cursor.execute(
                "UPDATE characters SET proxygroup_tid=NULL WHERE tid=?",
                (db_character["tid"],)
            )

            return Character(
                character.name,
                character.prefix,
                None,
                character.avatar
            )

    @enforce_annotations
    def update_character(self, user: User, character: Character, key: str, value) -> Character:
        """
        Update an attribute of a User's Character, then return it.

        Certain keys will be rejected to preserve DB integrity.

        :param user: The User to search.
        :type user: User
        :param character: The Character to update.
        :type character: Character
        :param key: The key to update.
        :type key: str
        :param value: The value to update it with.
        :return: The updated Character.
        """

        # a list of values that should always be rejected.
        banned = [
            "tid", # should never change
            "proxygroup_tid", # should be changed via group_character, not here
            "user_tid", # likely shouldn't change
        ]

        if key in banned:
            raise ValueError(f"Unable to update Character '{character.name}' with banned key '{key}'.")

        with sqlite3.connect(self.__data_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            db_user = db_get_user_row(cursor, user.uid)
            db_character = db_get_character(cursor, db_user["tid"], character.name)
            try:
                cursor.execute(
                    f"UPDATE characters SET {key}=? WHERE tid=?",
                    (value, db_character["tid"])
                )
            except sqlite3.OperationalError:
                raise ValueError("Invalid key name.")

            # we shouldn't trust the supplied objects over the DB, so fetch again.
            # must be done by TID, since there's a chance the name changed.
            db_character = cursor.execute(
                "SELECT * FROM characters WHERE tid=?",
                (db_character["tid"],)
            ).fetchall()[0]
            return Character(
                db_character["name"],
                db_character["prefix"],
                character.proxygroup_name, # except for the name, since that can't be changed here
                db_character["avatar"]
            )
