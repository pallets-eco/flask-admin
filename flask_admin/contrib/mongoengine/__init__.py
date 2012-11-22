try:
    import flask.ext.mongoengine
except ImportError:
    raise Exception('Please install flask-mongoengine in order to use mongoengine backend')

from .view import ModelView
