from typing import Optional

from flask import Flask
from sqlalchemy import Column
from sqlalchemy import Engine
from sqlalchemy import JSON
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import HSTORE
from sqlmodel import Field
from sqlmodel import Session

from flask_admin.base import Admin

from flask_admin.tests.sqlmodel import CustomModelView
from flask_admin.tests.sqlmodel import sqlmodel_base


def test_hstore(app: Flask, postgres_engine: Engine, postgres_admin: Admin):
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        # Define model
        class Model(sqlmodel_class, table=True):
            id: Optional[int]  = Field(default=None, primary_key=True)
            hstore_test: Optional[dict[str, str]] = Field(sa_column=Column(HSTORE))

        # Create table
        sqlmodel_class.metadata.create_all(postgres_engine)

        with Session(postgres_engine) as db_session:
            # Register admin view with standard SQLAlchemy session
            postgres_admin.add_view(CustomModelView(Model, db_session))

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


def test_json(app: Flask, postgres_engine: Engine, postgres_admin: Admin):
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class JSONModel(sqlmodel_class, table=True):
            id: Optional[int]  = Field(default=None, primary_key=True)
            json_test: Optional[dict] = Field(default=None, sa_column=Column(JSON))

        sqlmodel_class.metadata.create_all(postgres_engine)

        with Session(postgres_engine) as db_session:
            view = CustomModelView(JSONModel, db_session)
            postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/jsonmodel/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/jsonmodel/new/",
            data={"json_test": '{"test_key1": "test_value1"}'},
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


def test_citext(app: Flask, postgres_engine: Engine, postgres_admin: Admin):
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class CITextModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            citext_test: str = Field(sa_column=Column(CITEXT))

        # Ensure citext extension exists
        with postgres_engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))

        sqlmodel_class.metadata.create_all(postgres_engine)

        with Session(postgres_engine) as db_session:
            view = CustomModelView(CITextModel, db_session)
            postgres_admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/citextmodel/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/citextmodel/new/",
            data={"citext_test": "Foo"},
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
