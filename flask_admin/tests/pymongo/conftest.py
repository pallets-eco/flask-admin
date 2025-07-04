import os

import pytest
from pymongo import MongoClient

from flask_admin import Admin


@pytest.fixture
def db():
    client = MongoClient(host=os.getenv("MONGOCLIENT_HOST", "localhost"))
    db = client.tests
    yield db
    client.close()


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin
