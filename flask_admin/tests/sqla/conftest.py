import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin


@pytest.fixture(scope="function")
def app():
    # Overrides the `app` fixture in `flask_admin/tests/conftest.py` so that the `sqla`
    # directory/import path is configured as the root path for Flask. This will
    # cause the `templates` directory here to be used for template resolution.
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture
def db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    yield db


@pytest.fixture
def postgres_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:postgres@localhost/flask_admin_test"
    )
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db = SQLAlchemy(app)
    yield db


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin


@pytest.fixture
def postgres_admin(app, babel, postgres_db):
    admin = Admin(app)
    yield admin
