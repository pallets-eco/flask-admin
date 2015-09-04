try:
    import flask_mongoengine
except ImportError:
    raise Exception('Please install flask-mongoengine in order to use mongoengine backend')

from .view import ModelView
from .form import EmbeddedForm
