import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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
def db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    yield db

    with app.app_context():
        db.session.close()
        db.engine.dispose()


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin
