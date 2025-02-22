import pytest

from flask_admin import Admin
from flask_mongoengine import MongoEngine


@pytest.fixture
def db():
    db = MongoEngine()
    yield db


@pytest.fixture
def admin(app, babel, db):
    app.config['MONGODB_SETTINGS'] = {'DB': 'tests'}

    db.init_app(app)

    admin = Admin(app)
    yield admin
