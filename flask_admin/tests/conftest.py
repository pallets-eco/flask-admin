import sys
import typing as t

import flask_sqlalchemy
import pytest
from flask import Flask
from jinja2 import StrictUndefined
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import Session

from flask_admin import Admin
from flask_admin.contrib.sqla._types import T_SCOPED_SESSION
from flask_admin.contrib.sqla._types import T_SESSION_OR_DB
from flask_admin.contrib.sqla._types import T_SQLALCHEMY
from flask_admin.contrib.sqla._types import T_SQLALCHEMY_LITE

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
    def _sqlite_connect(dbapi_connection: t.Any, connection_record: t.Any) -> None:
        dbapi_connection.isolation_level = None

    def _sqlite_begin(conn: t.Any) -> None:
        conn.exec_driver_sql("BEGIN")

    @pytest.fixture(scope="session", autouse=True)
    def _sqlite_isolation() -> t.Generator[None, None, None]:
        event.listen(Engine, "connect", _sqlite_connect)
        event.listen(Engine, "begin", _sqlite_begin)
        yield
        event.remove(Engine, "begin", _sqlite_begin)
        event.remove(Engine, "connect", _sqlite_connect)


class SQLAProvider:
    def __init__(
        self,
    ) -> None:  # must be in __init__ to avoid leaking db instances btw tests
        from flask_sqlalchemy import SQLAlchemy

        self.db = SQLAlchemy()
        self.Base = self.db.Model

    def create_all(self) -> None:
        return self.db.create_all()

    def drop_all(self) -> None:
        return self.db.drop_all()


if t.TYPE_CHECKING:
    # Only used for type checking; at runtime SQLALiteProvider may not exist
    T_ANY_SQLA_PROVIDER = t.Union[SQLAProvider, "SQLALiteProvider"]
    T_SCOPED_SESSION_FLASK_SQLA = scoped_session[flask_sqlalchemy.Session.session]
else:
    T_ANY_SQLA_PROVIDER = object
    T_SCOPED_SESSION_FLASK_SQLA = scoped_session

sqla_db_exts: list[type[T_ANY_SQLA_PROVIDER]] = [SQLAProvider]

if HAS_SQLALCHEMY_2:

    class SQLALiteProvider:
        def __init__(self, engine_options: dict[str, t.Any] | None = None) -> None:
            # must be in __init__ to avoid leaking db instances btw tests
            from flask_sqlalchemy_lite import SQLAlchemy as SQLAlchemyLite

            # This ensures the engine created by lite-sqla is stable
            self.db = SQLAlchemyLite(engine_options=engine_options or {})

            class SqlAlchemyBase(DeclarativeBase):
                pass

            self.Base = SqlAlchemyBase

        def create_all(self) -> None:
            return self.Base.metadata.create_all(self.db.engine)

        def drop_all(self) -> None:
            return self.Base.metadata.drop_all(self.db.engine)

    sqla_db_exts.append(SQLALiteProvider)


@pytest.fixture(scope="function")
def app() -> t.Generator[Flask, t.Any, None]:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False
    app.jinja_env.undefined = StrictUndefined
    yield app


@pytest.fixture
def babel(app: Flask) -> t.Generator[object | None, None, None]:
    try:
        from flask_babel import Babel
    except ImportError:
        yield None
        return

    yield Babel(app)


@pytest.fixture
def admin(app: Flask, babel: t.Any | None) -> t.Generator[Admin, t.Any, None]:
    admin = Admin(app)
    yield admin


def configure_sqla(app: Flask, uri: str, request: pytest.FixtureRequest) -> None:
    """
    Sets common app config.
    Function calling must have @pytest.fixture(params=sqla_db_exts)
    """
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    param: type[t.Any] = request.param
    is_flask_sqlalchemy = param is SQLAProvider
    if is_flask_sqlalchemy:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
    else:
        app.config["SQLALCHEMY_ENGINES"] = {"default": uri}


@pytest.fixture(params=sqla_db_exts)
def sqla_db_ext(
    request: pytest.FixtureRequest, app: Flask
) -> t.Generator[T_ANY_SQLA_PROVIDER, None, None]:
    uri = "sqlite:///:memory:"
    configure_sqla(app, uri, request)
    provider_cls: type[t.Any] = request.param
    p: T_ANY_SQLA_PROVIDER = provider_cls()
    p.db.init_app(app)

    with app.app_context():
        yield p


@pytest.fixture(
    params=[
        pytest.param("session", id="with_session_deprecated"),
        pytest.param("db", id="with_db"),
    ]
)
def session_or_db(request: pytest.FixtureRequest) -> T_SESSION_OR_DB:
    return request.param


T_LITERAL_SESSION_OR_DB = t.Literal["session", "db"]


@t.overload
def skip_or_return_session_or_db(
    extension: "SQLAProvider",
    string: t.Literal["session"],
) -> T_SCOPED_SESSION: ...


@t.overload
def skip_or_return_session_or_db(
    extension: "SQLAProvider",
    string: t.Literal["db"],
) -> T_SQLALCHEMY: ...


@t.overload
def skip_or_return_session_or_db(
    extension: "SQLALiteProvider",
    string: t.Literal["session"],
) -> t.NoReturn: ...  # never actually returns (pytest.skip)


@t.overload
def skip_or_return_session_or_db(
    extension: "SQLALiteProvider",
    string: t.Literal["db"],
) -> T_SQLALCHEMY_LITE: ...


def skip_or_return_session_or_db(
    extension: T_ANY_SQLA_PROVIDER, string: T_LITERAL_SESSION_OR_DB
) -> (
    T_SCOPED_SESSION
    | Session
    | T_SQLALCHEMY
    | T_SQLALCHEMY_LITE
    | T_SCOPED_SESSION_FLASK_SQLA
):
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
