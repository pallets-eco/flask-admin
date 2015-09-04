try:
    import pymongo
except ImportError:
    raise Exception('Please install pymongo in order to use pymongo integration')

from .view import ModelView
