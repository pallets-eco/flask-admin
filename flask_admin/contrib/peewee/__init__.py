try:
    import peewee
    import wtfpeewee
except ImportError:
    raise Exception('Please install peewee and wtf-peewee packages in order to use peewee integration')

from .view import ModelView
