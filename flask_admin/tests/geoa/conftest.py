import os

import pytest

from flask_admin.tests.conftest import close_db
from flask_admin.tests.conftest import configure_sqla
from flask_admin.tests.conftest import sqla_db_exts


@pytest.fixture(params=sqla_db_exts)
def sqla_db_ext(request, app):
    # need postgres for spatial types
    uri = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )

    configure_sqla(app, uri, request)

    p = request.param()
    p.db.init_app(app)

    with app.app_context():
        yield p
        close_db(app, p)
