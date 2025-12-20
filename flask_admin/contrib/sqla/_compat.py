import typing as t
import warnings

from flask_admin.contrib.sqla._types import T_SCOPED_SESSION
from flask_admin.contrib.sqla._types import T_SESSION
from flask_admin.contrib.sqla._types import T_SESSION_OR_DB
from flask_admin.contrib.sqla._types import T_SQLALCHEMY
from flask_admin.contrib.sqla._types import T_SQLALCHEMY_LITE


@t.overload
def _warn_session_deprecation(session: None, warn: bool = True) -> None: ...


@t.overload
def _warn_session_deprecation(
    session: T_SESSION_OR_DB, warn: bool = True
) -> T_SESSION_OR_DB: ...


def _warn_session_deprecation(session, warn: bool = True):
    """
    Warn about deprecation of passing session objects directly.
    Raise error if session is from Flask-SQLAlchemy-Lite.
    """
    if hasattr(session, "session"):
        if isinstance(session, T_SQLALCHEMY_LITE):
            # see::
            # https://github.com/pallets-eco/flask-admin/issues/2585
            # https://github.com/pallets-eco/flask-admin/pull/2680
            raise TypeError(
                "Passing a session object directly is not supported with "
                "Flask-SQLAlchemy-Lite. "
                "Please pass the SQLAlchemy db object instead. "
                "Example: ModelView(User, db) instead of ModelView(User, db.session)"
            )
        if warn:
            warnings.warn(
                "Passing a session object directly is deprecated and will be "
                "removed in version 3.0. "
                "Please pass the SQLAlchemy db object instead. "
                "Note: the parameter will be renamed from 'session' to 'db' in version "
                "3.0. "
                "Example: ModelView(User, db) instead of ModelView(User, db.session)",
                DeprecationWarning,
                stacklevel=3,
            )
    return session


@t.overload
def _get_deprecated_session(session: None) -> None: ...


@t.overload
def _get_deprecated_session(
    session: T_SESSION_OR_DB,
) -> T_SCOPED_SESSION | T_SESSION: ...


def _get_deprecated_session(
    session,
):
    """
    Returns the session if passed directly, session.session otherwise.
    """
    if (T_SQLALCHEMY is not None and isinstance(session, T_SQLALCHEMY)) or (
        T_SQLALCHEMY_LITE is not None and isinstance(session, T_SQLALCHEMY_LITE)
    ):
        return session.session
    return session
