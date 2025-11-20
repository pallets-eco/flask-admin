import typing as t

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.query import Query

if t.TYPE_CHECKING:  # sqlalchemy 2.x types are subscriptable
    T_SQLALCHEMY_QUERY = Query[t.Any]
    T_SCOPED_SESSION = scoped_session[t.Any]
else:  # sqlalchemy 1.x types are not subscriptable
    T_SQLALCHEMY_QUERY = Query
    T_SCOPED_SESSION = scoped_session
