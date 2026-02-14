from citext import CIText
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.dialects.postgresql import JSON

from .test_basic import CustomModelView


def test_hstore(app, sqla_postgres_db_ext, postgres_admin, session_or_db):
    with app.app_context():

        class Model(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            hstore_test = Column(HSTORE)

        sqla_postgres_db_ext.create_all()

        param = (
            sqla_postgres_db_ext.db.session
            if session_or_db == "session"
            else sqla_postgres_db_ext.db
        )
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


def test_json(app, sqla_postgres_db_ext, postgres_admin, session_or_db):
    with app.app_context():

        class JSONModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "json_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            json_test = Column(JSON)

        sqla_postgres_db_ext.create_all()

        param = (
            sqla_postgres_db_ext.db.session
            if session_or_db == "session"
            else sqla_postgres_db_ext.db
        )
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


def test_citext(app, sqla_postgres_db_ext, postgres_admin, session_or_db):
    with app.app_context():

        class CITextModel(sqla_postgres_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "citext_model"
            id = Column(Integer, primary_key=True, autoincrement=True)
            citext_test = Column(CIText)

        with sqla_postgres_db_ext.db.engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        sqla_postgres_db_ext.create_all()

        param = (
            sqla_postgres_db_ext.db.session
            if session_or_db == "session"
            else sqla_postgres_db_ext.db
        )
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


def test_boolean_filters(app, sqla_postgres_db_ext, postgres_admin, session_or_db):
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

        param = (
            sqla_postgres_db_ext.db.session
            if session_or_db == "session"
            else sqla_postgres_db_ext.db
        )
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
