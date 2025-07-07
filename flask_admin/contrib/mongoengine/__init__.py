# flake8: noqa
try:
    import mongoengine  # type: ignore
except ImportError:
    raise Exception(
        "Could not import `mongoengine`. "
        "Enable `mongoengine` integration by installing `flask-admin[mongoengine]`"
    )

from .view import ModelView
from .form import EmbeddedForm
