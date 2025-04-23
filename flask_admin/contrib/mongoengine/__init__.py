# flake8: noqa
try:
    import mongoengine
except ImportError:
    raise Exception("Please install mongoengine in order to use mongoengine backend")

from .view import ModelView
from .form import EmbeddedForm
