import typing as t

import pytest
from flask import Flask
from peewee import SqliteDatabase

from flask_admin import Admin


@pytest.fixture
def db(app: Flask) -> t.Generator[SqliteDatabase, t.Any, None]:
    db = SqliteDatabase(":memory:")
    yield db
    with app.app_context():
        db.close()


@pytest.fixture
def admin(
    app: Flask, babel: object | None, db: SqliteDatabase
) -> t.Generator[Admin, None, None]:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"

    admin = Admin(app)
    yield admin
