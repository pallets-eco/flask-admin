import typing as t

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.query import Query

try:
    from flask_sqlalchemy_lite import SQLAlchemy as T_SQLALCHEMY_LITE
except ImportError:
    T_SQLALCHEMY_LITE: t.Any | None = None  # type: ignore[no-redef]

try:
    from flask_sqlalchemy import SQLAlchemy as T_SQLALCHEMY
    from flask_sqlalchemy.session import Session as T_SESSION
except ImportError:
    T_SQLALCHEMY: t.Any | None = None  # type: ignore[no-redef]


if t.TYPE_CHECKING:  # sqlalchemy 2.x types are subscriptable
    T_SQLALCHEMY_QUERY = Query[t.Any]
    T_SCOPED_SESSION = scoped_session[T_SESSION]

else:  # sqlalchemy 1.x types are not subscriptable
    T_SQLALCHEMY_QUERY = Query
    T_SCOPED_SESSION = scoped_session


T_SESSION_OR_DB = T_SCOPED_SESSION | T_SQLALCHEMY | T_SQLALCHEMY_LITE
