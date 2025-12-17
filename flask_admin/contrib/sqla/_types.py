import typing as t

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

if t.TYPE_CHECKING:  # sqlalchemy 2.x types are subscriptable
    T_SQLALCHEMY_QUERY = Query[t.Any]
    T_SCOPED_SESSION = scoped_session[t.Any]

else:  # sqlalchemy 1.x types are not subscriptable
    T_SQLALCHEMY_QUERY = Query
    T_SCOPED_SESSION = scoped_session

try:
    from flask_sqlalchemy_lite import SQLAlchemy as T_SQLALCHEMY_LITE
except ImportError:
    T_SQLALCHEMY_LITE: t.Any | None = None  # type: ignore[no-redef]

try:
    from flask_sqlalchemy import SQLAlchemy as T_SQLALCHEMY
except ImportError:
    T_SQLALCHEMY: t.Any | None = None  # type: ignore[no-redef]


T_SESSION = Session
T_SESSION_OR_DB = T_SCOPED_SESSION | T_SESSION | T_SQLALCHEMY | T_SQLALCHEMY_LITE
