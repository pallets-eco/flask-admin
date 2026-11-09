import os
from collections.abc import Generator

import pytest
from flask import Flask
from pytest import FixtureRequest

from flask_admin.tests.conftest import configure_sqla
from flask_admin.tests.conftest import sqla_db_exts
from flask_admin.tests.conftest import SQLAProviderProtocol


@pytest.fixture(params=sqla_db_exts)
def sqla_db_ext(
    request: FixtureRequest, app: Flask
) -> Generator[SQLAProviderProtocol, None, None]:
    # need postgres for spatial types
    uri = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )

    configure_sqla(app, uri, request)

    p = request.param()
    p.db.init_app(app)

    yield p
