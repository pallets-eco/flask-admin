import pytest
from flask import Flask
from jinja2 import StrictUndefined

from flask_admin import Admin


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False
    app.jinja_env.undefined = StrictUndefined
    yield app


@pytest.fixture
def babel(app):
    babel = None
    try:
        from flask_babel import Babel

        babel = Babel(app)
    except ImportError:
        pass

    yield babel


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin


session_or_db = pytest.mark.parametrize(
    "session_or_db",
    [
        pytest.param("session", id="with_session_deprecated"),
        pytest.param("db", id="with_db"),
    ],
)
