import os
import typing as t

import pytest
from flask import Flask
from mongoengine import connect
from mongoengine import disconnect

from flask_admin import Admin
from flask_admin.contrib.sqla._types import T_SESSION_OR_DB


@pytest.fixture
def db():
    db_name = "tests"
    host = os.getenv("MONGOCLIENT_HOST", "localhost")
    connect(db=db_name, host=host, uuidRepresentation="standard")
    yield db
    disconnect()


@pytest.fixture
def admin(
    app: Flask, babel: object | None, db: T_SESSION_OR_DB
) -> t.Generator[Admin, t.Any, None]:
    admin = Admin(app)
    yield admin
