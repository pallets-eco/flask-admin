import typing as t

# compatibility layer for pymongo 3 and 4
try:
    from pymongo import MongoClient
    from pymongo.synchronous.collection import Collection
    from pymongo.synchronous.cursor import Cursor
    from pymongo.synchronous.database import Database

    T_PYMONGO_CLIENT = MongoClient[t.Any]
    T_PYMONGO_COLLECTION = Collection[t.Any]
    T_PYMONGO_CURSOR = Cursor[t.Any]
    T_PYMONGO_DB = Database[t.Any]

except ImportError:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    from pymongo.cursor import Cursor
    from pymongo.database import Database

    T_PYMONGO_CLIENT = MongoClient  # type: ignore[misc]
    T_PYMONGO_COLLECTION = Collection  # type: ignore[misc]
    T_PYMONGO_CURSOR = Cursor  # type: ignore[misc]
    T_PYMONGO_DB = Database  # type: ignore[misc]
