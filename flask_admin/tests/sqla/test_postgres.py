import os
import typing as t

import pytest
from citext import CIText
from flask import Flask
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.dialects.postgresql import JSON

from ... import Admin
from ..conftest import configure_sqla
from ..conftest import skip_or_return_session_or_db
from ..conftest import sqla_db_exts
from ..conftest import SQLAProvider
from ..conftest import T_ANY_SQLA_PROVIDER
from ..conftest import T_LITERAL_SESSION_OR_DB
from .test_basic import CustomModelView


def test_hstore(
    app: Flask,
    sqla_postgres_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class Model(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            hstore_test = Column(HSTORE)

        sqla_postgres_db_ext.create_all()

        param = skip_or_return_session_or_db(sqla_postgres_db_ext, session_or_db)
        view = CustomModelView(Model, param)
        postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/model/new/",
            data={"hstore_test-0-key": "test_val1", "hstore_test-0-value": "test_val2"},
        )
        assert rv.status_code == 302

        rv = client.get("/admin/model/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_val1" in data
        assert "test_val2" in data

        rv = client.get("/admin/model/edit/?id=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_val1" in data
        assert "test_val2" in data


def test_json(
    app: Flask,
    sqla_postgres_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class JSONModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "json_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            json_test = Column(JSON)

        sqla_postgres_db_ext.create_all()

        param = skip_or_return_session_or_db(sqla_postgres_db_ext, session_or_db)
        view = CustomModelView(JSONModel, param)
        postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/jsonmodel/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/jsonmodel/new/",
            data={
                "json_test": '{"test_key1": "test_value1"}',
            },
        )
        assert rv.status_code == 302

        rv = client.get("/admin/jsonmodel/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "json_test" in data
        assert "{&#34;test_key1&#34;: &#34;test_value1&#34;}" in data

        rv = client.get("/admin/jsonmodel/edit/?id=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "json_test" in data
        assert (
            '>{"test_key1": "test_value1"}<' in data
            or "{&#34;test_key1&#34;: &#34;test_value1&#34;}<" in data
        )


def test_citext(
    app: Flask,
    sqla_postgres_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class CITextModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "citext_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            citext_test = Column(CIText)

        with sqla_postgres_db_ext.db.engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        sqla_postgres_db_ext.create_all()

        param = skip_or_return_session_or_db(sqla_postgres_db_ext, session_or_db)
        view = CustomModelView(CITextModel, param)
        postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/citextmodel/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/citextmodel/new/",
            data={
                "citext_test": "Foo",
            },
        )
        assert rv.status_code == 302

        rv = client.get("/admin/citextmodel/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "citext_test" in data
        assert "Foo" in data

        rv = client.get("/admin/citextmodel/edit/?id=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert 'name="citext_test"' in data
        assert ">Foo</" in data or ">\nFoo</" in data or ">\r\nFoo</" in data


def test_boolean_filters(
    app: Flask,
    sqla_postgres_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    """
    Test that boolean filters work correctly with PostgreSQL.
    This is particularly important for psycopg3 compatibility,
    which is stricter about type coercion than psycopg2.
    """
    with app.app_context():

        class BoolModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "bool_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            bool_field = Column(Boolean, nullable=False)
            name = Column(String(50))

        sqla_postgres_db_ext.create_all()

        # Add test data
        sqla_postgres_db_ext.db.session.add(
            BoolModel(bool_field=True, name="true_val_1")
        )
        sqla_postgres_db_ext.db.session.add(
            BoolModel(bool_field=False, name="false_val_1")
        )
        sqla_postgres_db_ext.db.session.add(
            BoolModel(bool_field=False, name="false_val_2")
        )
        sqla_postgres_db_ext.db.session.commit()

        param = skip_or_return_session_or_db(sqla_postgres_db_ext, session_or_db)
        view = CustomModelView(BoolModel, param, column_filters=["bool_field"])
        postgres_admin.add_view(view)

        client = app.test_client()

        # Verify filters are set up
        assert view._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view._filter_groups["Bool Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
        ]

        # Test boolean equals True (value="1")
        rv = client.get("/admin/boolmodel/?flt0_0=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "true_val_1" in data
        assert "false_val_1" not in data
        assert "false_val_2" not in data

        # Test boolean equals False (value="0")
        rv = client.get("/admin/boolmodel/?flt0_0=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "true_val_1" not in data
        assert "false_val_1" in data
        assert "false_val_2" in data

        # Test boolean not equals True (value="1")
        rv = client.get("/admin/boolmodel/?flt0_1=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "true_val_1" not in data
        assert "false_val_1" in data
        assert "false_val_2" in data

        # Test boolean not equals False (value="0")
        rv = client.get("/admin/boolmodel/?flt0_1=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "true_val_1" in data
        assert "false_val_1" not in data
        assert "false_val_2" not in data


def test_multiple_delete_integer_pk(
    app: Flask,
    sqla_postgres_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class IntModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "test_bulk_delete_int_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String(50))

        sqla_postgres_db_ext.drop_all()
        sqla_postgres_db_ext.create_all()

        m1 = IntModel(name="a")
        m2 = IntModel(name="b")
        m3 = IntModel(name="c")
        sqla_postgres_db_ext.db.session.add_all([m1, m2, m3])
        sqla_postgres_db_ext.db.session.commit()

        param = skip_or_return_session_or_db(sqla_postgres_db_ext, session_or_db)
        view = CustomModelView(IntModel, param)
        postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.post(
            "/admin/intmodel/action/",
            data=dict(action="delete", rowid=[str(m1.id), str(m2.id)]),
        )
        assert rv.status_code == 302
        assert sqla_postgres_db_ext.db.session.query(IntModel).count() == 1
        model = sqla_postgres_db_ext.db.session.query(IntModel).first()
        assert model is not None
        assert model.id == m3.id


@pytest.fixture(params=sqla_db_exts)
def sqla_postgres_psycopg3_db_ext(
    app: Flask, request: pytest.FixtureRequest
) -> t.Generator[T_ANY_SQLA_PROVIDER, None, None]:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        pytest.skip("psycopg (v3) is not installed")

    from sqlalchemy.dialects import registry

    try:
        registry.load("postgresql.psycopg")
    except Exception:
        pytest.skip("SQLAlchemy dialect postgresql.psycopg is not available")

    base_uri = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://postgres:postgres@localhost/flask_admin_test",
    )
    if "://" in base_uri:
        _, rest = base_uri.split("://", 1)
        uri = f"postgresql+psycopg://{rest}"
    else:
        uri = "postgresql+psycopg://postgres:postgres@localhost/flask_admin_test"

    configure_sqla(app, uri, request)
    provider_class = request.param
    if provider_class != SQLAProvider:
        provider = provider_class(engine_options={})
    else:
        provider = provider_class()

    provider.db.init_app(app)

    with app.app_context():
        try:
            yield provider
        finally:
            provider.db.session.close()
            if hasattr(provider.db, "engine"):
                provider.db.engine.dispose()
            elif hasattr(provider.db, "engines"):
                engines = getattr(provider.db, "_engines", None) or getattr(
                    provider.db, "engines", {}
                )
                for eng in engines.values():
                    eng.dispose()


def test_multiple_delete_integer_pk_psycopg3(
    app: Flask,
    sqla_postgres_psycopg3_db_ext: T_ANY_SQLA_PROVIDER,
    postgres_admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class IntModel(sqla_postgres_psycopg3_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "test_bulk_delete_int_model_psycopg3"
            id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String(50))

        sqla_postgres_psycopg3_db_ext.drop_all()
        sqla_postgres_psycopg3_db_ext.create_all()

        m1 = IntModel(name="a")
        m2 = IntModel(name="b")
        m3 = IntModel(name="c")
        sqla_postgres_psycopg3_db_ext.db.session.add_all([m1, m2, m3])
        sqla_postgres_psycopg3_db_ext.db.session.commit()

        param = skip_or_return_session_or_db(
            sqla_postgres_psycopg3_db_ext, session_or_db
        )
        view = CustomModelView(IntModel, param)
        postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.post(
            "/admin/intmodel/action/",
            data=dict(action="delete", rowid=[str(m1.id), str(m2.id)]),
        )
        assert rv.status_code == 302
        assert sqla_postgres_psycopg3_db_ext.db.session.query(IntModel).count() == 1
        model = sqla_postgres_psycopg3_db_ext.db.session.query(IntModel).first()
        assert model is not None
        assert model.id == m3.id
