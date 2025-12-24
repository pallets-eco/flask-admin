import pytest
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    yield db

    with app.app_context():
        db.session.remove()
