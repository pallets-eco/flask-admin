# flake8: noqa
try:
    import flask_mongoengine
except ImportError:
    raise Exception(
        'Could not import `flask-mongoengine`. '
        'Enable `mongoengine` integration by installing `flask-admin[mongoengine]`'
    )

from .view import ModelView
from .form import EmbeddedForm
