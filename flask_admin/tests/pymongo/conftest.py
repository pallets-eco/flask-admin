import os
import typing as t

import pytest
from flask import Flask
from pymongo import MongoClient

from flask_admin import Admin
from flask_admin.contrib.pymongo._types import T_PYMONGO_DB


@pytest.fixture
def db() -> t.Generator[T_PYMONGO_DB, None, None]:
    client: MongoClient[t.Any] = MongoClient(
        host=os.getenv("MONGOCLIENT_HOST", "localhost")
    )
    db = client.tests
    yield db
    client.close()


@pytest.fixture
def admin(
    app: Flask, babel: object | None, db: T_PYMONGO_DB
) -> t.Generator[Admin, None, None]:
    admin = Admin(app)
    yield admin
