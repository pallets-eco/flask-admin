# flake8: noqa
try:
    import pymongo
except ImportError:
    raise Exception(
        "Could not import `pymongo`. "
        "Enable `pymongo` integration by installing `flask-admin[pymongo]`"
    )

from .view import ModelView
