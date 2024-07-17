import pytest

from flask_admin import Admin
import peewee


@pytest.fixture
def db():
    db = peewee.SqliteDatabase(':memory:')
    yield db


@pytest.fixture
def admin(app, babel, db):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

    admin = Admin(app)
    yield admin
