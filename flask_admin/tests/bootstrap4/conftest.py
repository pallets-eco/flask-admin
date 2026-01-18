import typing as t

import pytest

try:  # flask-sqlalchemy-lite is compatible only with SQLAlchemy 2.x
    from sqlalchemy.orm import DeclarativeBase

    HAS_SQLALCHEMY_2 = True
except ImportError:
    HAS_SQLALCHEMY_2 = False


class SQLAProvider:
    from flask_sqlalchemy import SQLAlchemy

    db = SQLAlchemy()
    Base = db.Model

    def create_all(self):
        return self.db.create_all()


providers: list[type[t.Any]] = [SQLAProvider]

if HAS_SQLALCHEMY_2:

    class SQLALiteProvider:
        from flask_sqlalchemy_lite import SQLAlchemy

        db = SQLAlchemy()

        class SqlAlchemyBase(DeclarativeBase):
            pass

        Base = SqlAlchemyBase

        def create_all(self):
            return self.Base.metadata.create_all(self.db.engine)

    providers.append(SQLALiteProvider)


@pytest.fixture(params=providers)
def provider(request, app):
    # flask_sqlalchemy legacy and flask_sqlalchemy_lite have different config keys
    if request.param == SQLAProvider:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///default.sqlite"
    else:
        app.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:///default.sqlite"}
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    p = request.param()
    p.db.init_app(app)

    with app.app_context():
        yield p
        if hasattr(p.db, "session") and hasattr(p.db.session, "remove"):
            p.db.session.remove()
        else:
            # If a SQLAlchemy extension was registered, dispose of all its engines to
            # avoid ResourceWarning: unclosed sqlite3.Connection.
            # source: https://github.com/pallets-eco/flask-sqlalchemy-lite/blob/main/tests/conftest.py
            try:
                db = app.extensions["sqlalchemy"]
            except KeyError:
                pass
            else:
                with app.app_context():
                    engines = db.engines.values()

                for engine in engines:
                    engine.dispose()
