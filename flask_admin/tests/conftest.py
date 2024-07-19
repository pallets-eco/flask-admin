import pytest
from flask import Flask

from flask_admin import Admin


@pytest.fixture(scope='function')
def app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['WTF_CSRF_ENABLED'] = False

    yield app


@pytest.fixture
def babel(app):
    try:
        from flask_babel import Babel
        _ = Babel(app)
    except ImportError:
        pass

    yield babel


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin
