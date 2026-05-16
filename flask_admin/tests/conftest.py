import sys
import typing as t

import pytest
from flask import Flask
from jinja2 import StrictUndefined
from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask_admin import Admin

# flask-sqlalchemy-lite is compatible only with SQLAlchemy 2.x
# remove conditional imports when dropping support for SQLAlchemy 1.x
try:
    from sqlalchemy.orm import DeclarativeBase

    HAS_SQLALCHEMY_2 = True
except ImportError:
    HAS_SQLALCHEMY_2 = False

if sys.version_info < (3, 12):
    # Fix sqlite3 driver's handling of transactions.
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#sqlite-transactions
    def _sqlite_connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    def _sqlite_begin(conn):
        conn.exec_driver_sql("BEGIN")

    @pytest.fixture(scope="session", autouse=True)
    def _sqlite_isolation():
        event.listen(Engine, "connect", _sqlite_connect)
        event.listen(Engine, "begin", _sqlite_begin)
        yield
        event.remove(Engine, "begin", _sqlite_begin)
        event.remove(Engine, "connect", _sqlite_connect)


class SQLAProvider:
    def __init__(self):  # must be in __init__ to avoid leaking db instances btw tests
        from flask_sqlalchemy import SQLAlchemy

        self.db = SQLAlchemy()
        self.Base = self.db.Model

    def create_all(self):
        return self.db.create_all()

    def drop_all(self):
        return self.db.drop_all()


sqla_db_exts: list[type[t.Any]] = [SQLAProvider]

if HAS_SQLALCHEMY_2:

    class SQLALiteProvider:
        def __init__(self, engine_options: dict[str, t.Any] | None = None):
            # must be in __init__ to avoid leaking db instances btw tests
            from flask_sqlalchemy_lite import SQLAlchemy as SQLAlchemyLite

            # This ensures the engine created by lite-sqla is stable
            self.db = SQLAlchemyLite(engine_options=engine_options or {})

            class SqlAlchemyBase(DeclarativeBase):
                pass

            self.Base = SqlAlchemyBase

        def create_all(self):
            return self.Base.metadata.create_all(self.db.engine)

        def drop_all(self):
            return self.Base.metadata.drop_all(self.db.engine)

    sqla_db_exts.append(SQLALiteProvider)


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False
    app.jinja_env.undefined = StrictUndefined
    yield app


@pytest.fixture
def babel(app):
    babel = None
    try:
        from flask_babel import Babel

        babel = Babel(app)
    except ImportError:
        pass

    yield babel


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin


def configure_sqla(app: Flask, uri: str, request: pytest.FixtureRequest) -> None:
    """
    Sets common app config.
    Function calling must have @pytest.fixture(params=sqla_db_exts)
    """
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    is_flask_sqlalchemy = request.param == SQLAProvider
    if is_flask_sqlalchemy:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
    else:
        app.config["SQLALCHEMY_ENGINES"] = {"default": uri}


@pytest.fixture(params=sqla_db_exts)
def sqla_db_ext(request, app):
    uri = "sqlite:///:memory:"
    configure_sqla(app, uri, request)
    p = request.param()
    p.db.init_app(app)

    with app.app_context():
        yield p


@pytest.fixture(
    params=[
        pytest.param("session", id="with_session_deprecated"),
        pytest.param("db", id="with_db"),
    ]
)
def session_or_db(request):
    return request.param


def skip_or_return_session_or_db(
    extension: "SQLAProvider | SQLALiteProvider", string: t.Literal["session", "db"]
) -> t.Any:
    """
    Helper function to skip tests (when using SQLALiteProvider and deprecated session)
    or to return the appropriate parameter (extension.db.session or extension.db) for
    other cases.

    Returns
    -------
    object
        - `extension.db.session` when `string == "session"` and the provider supports it
        - `extension.db` when any other object is requested.

    Raises
    ------
    pytest.skip
        If `"session"` is requested while using `SQLALiteProvider`.
    """
    if extension.__class__.__name__ == "SQLALiteProvider" and string == "session":
        pytest.skip("SQLALiteProvider does not support session")
    elif string == "session":
        return extension.db.session
    else:
        return extension.db
