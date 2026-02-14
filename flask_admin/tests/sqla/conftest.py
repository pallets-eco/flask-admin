import os
import sys
import typing as t

import pytest
from flask import Flask

from flask_admin import Admin
from flask_admin.tests.conftest import close_db
from flask_admin.tests.conftest import configure_sqla
from flask_admin.tests.conftest import sqla_db_exts
from flask_admin.tests.conftest import SQLAProvider


@pytest.fixture(scope="function")
def app():
    # Overrides the `app` fixture in `flask_admin/tests/conftest.py` so that the `sqla`
    # directory/import path is configured as the root path for Flask. This will
    # cause the `templates` directory here to be used for template resolution.
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture(params=sqla_db_exts)
def sqla_db_ext_with_binds(request, app_with_binds):
    uri = "sqlite:///file:mem?mode=memory&cache=shared"
    configure_sqla(app_with_binds, uri, request)

    # Instantiate the provider (SQLAProvider or SQLALiteProvider)
    p = request.param()
    p.db.init_app(app_with_binds)

    with app_with_binds.app_context():
        yield p
        close_db(app_with_binds, p)


@pytest.fixture
def app_with_binds(app):
    # flask-sqlalchemy
    app.config["SQLALCHEMY_BINDS"] = {"other": "sqlite:///"}
    # flask-sqlalchemy-lite
    app.config["SQLALCHEMY_ENGINES"] = {
        "default": "sqlite:///file:mem?mode=memory&cache=shared",
        "other": "sqlite:///file:mem?mode=memory&cache=shared",
    }
    yield app


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin


@pytest.fixture
def postgres_admin(app, babel):
    admin = Admin(app)
    yield admin


@pytest.fixture(params=sqla_db_exts)
def sqla_postgres_db_ext(app, request):
    uri = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )
    configure_sqla(app, uri, request)
    # SQLALiteProvider needs special handling for Python 3.12+ with SQLite
    provider_class = request.param
    if provider_class != SQLAProvider:
        engine_options: dict[str, t.Any] = {}
        if sys.version_info >= (3, 12) and uri.startswith("sqlite"):
            engine_options["connect_args"] = {"autocommit": False}
        provider = provider_class(engine_options=engine_options)
    else:
        # SQLAProvider (legacy) uses app.config directly
        provider = provider_class()

    provider.db.init_app(app)

    with app.app_context():
        yield provider
        close_db(app, provider)
