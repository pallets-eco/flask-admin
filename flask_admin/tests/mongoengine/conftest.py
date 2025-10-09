import os

import pytest
from mongoengine import connect
from mongoengine import disconnect

from flask_admin import Admin


@pytest.fixture
def db():
    db_name = "tests"
    host = os.getenv("MONGOCLIENT_HOST", "localhost")
    connect(db=db_name, host=host, uuidRepresentation="standard")
    yield db
    disconnect()


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin
