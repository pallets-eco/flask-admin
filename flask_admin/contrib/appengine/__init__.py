# flake8: noqa
try:
    import wtforms_appengine
except ImportError:
    raise Exception(
        'Could not import `wtforms-appengine`. '
        'Enable `appengine` integration by installing `flask-admin[appengine]`'
    )

from .view import ModelView
