import os
from collections.abc import Generator
from typing import Any
from typing import Optional

import pytest
from flask import Flask
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry
from sqlmodel import create_engine
from sqlmodel import SQLModel

from flask_admin import Admin


@pytest.fixture
def babel(app: Flask) -> Generator[Optional[Any], None, None]:
    babel = None
    try:
        from flask_babel import Babel

        babel = Babel(app)
    except ImportError:
        pass
    yield babel


@pytest.fixture(scope="function")
def app() -> Generator[Flask, None, None]:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture(scope="function")
def engine(app: Flask) -> Generator[Engine, None, None]:
    # In-memory SQLite database
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    engine = create_engine("sqlite://")
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def sqlmodel_base() -> type[SQLModel]:
    """Create a fresh SQLModel base class for each test to avoid class name conflicts"""
    # Create a fresh registry and metadata for complete isolation
    test_registry = registry()

    # Create a new SQLModel base class with its own registry
    class CleanSQLModel(SQLModel, registry=test_registry):
        pass

    return CleanSQLModel


@pytest.fixture(scope="function")
def postgres_engine(app: Flask) -> Generator[Engine, None, None]:
    # PostgreSQL test database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    yield engine
    engine.dispose()


@pytest.fixture
def admin(app: Flask, babel: Optional[Any]) -> Admin:
    return Admin(app)


@pytest.fixture
def postgres_admin(app: Flask, babel: Optional[Any]) -> Generator[Admin, None, None]:
    admin = Admin(app)
    yield admin
