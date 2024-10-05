# flake8: noqa
try:
    import wtforms_appengine
except ImportError:
    raise Exception('Please install wtforms_appengine in order to use appengine backend')

from .view import ModelView
