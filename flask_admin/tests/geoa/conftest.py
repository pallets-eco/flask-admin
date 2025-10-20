import os

import pytest
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin


@pytest.fixture
def db(app):
    db = SQLAlchemy()
    yield db
    with app.app_context():
        db.session.close()
        db.engine.dispose()


@pytest.fixture
def admin(app, babel, db):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.app_context().push()

    admin = Admin(app)
    yield admin
