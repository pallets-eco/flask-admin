import os
import typing as t

import pytest
from flask import Flask
from mongoengine import connect
from mongoengine import disconnect

from flask_admin import Admin


@pytest.fixture
def db() -> t.Generator[None, t.Any, None]:
    db_name = "tests"
    host = os.getenv("MONGOCLIENT_HOST", "localhost")
    connect(db=db_name, host=host, uuidRepresentation="standard")
    try:
        yield
    finally:
        disconnect()


@pytest.fixture
def admin(
    app: Flask, babel: object | None, db: t.Any
) -> t.Generator[Admin, t.Any, None]:
    admin = Admin(app)
    yield admin
