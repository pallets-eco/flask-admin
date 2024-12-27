import pytest
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin


@pytest.fixture
def db():
    db = SQLAlchemy()
    yield db


@pytest.fixture
def admin(app, babel, db):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:postgres@localhost/flask_admin_test"
    )
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.app_context().push()

    admin = Admin(app)
    yield admin
