# flake8: noqa
try:
    import peewee
    import wtfpeewee
except ImportError:
    raise Exception(
        "Could not import `peewee` or `wtfpeewee`. "
        "Enable `peewee` integration by installing `flask-admin[peewee]`"
    )

from .view import ModelView
