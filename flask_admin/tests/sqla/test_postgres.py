from citext import CIText
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.dialects.postgresql import JSON

from .test_basic import CustomModelView


def test_hstore(app, postgres_db, postgres_admin):
    with app.app_context():

        class Model(postgres_db.Model):
            id = postgres_db.Column(
                postgres_db.Integer, primary_key=True, autoincrement=True
            )
            hstore_test = postgres_db.Column(HSTORE)

        postgres_db.create_all()

        view = CustomModelView(Model, postgres_db.session)
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


def test_json(app, postgres_db, postgres_admin):
    with app.app_context():

        class JSONModel(postgres_db.Model):
            id = postgres_db.Column(
                postgres_db.Integer, primary_key=True, autoincrement=True
            )
            json_test = postgres_db.Column(JSON)

        postgres_db.create_all()

        view = CustomModelView(JSONModel, postgres_db.session)
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


def test_citext(app, postgres_db, postgres_admin):
    with app.app_context():

        class CITextModel(postgres_db.Model):
            id = postgres_db.Column(
                postgres_db.Integer, primary_key=True, autoincrement=True
            )
            citext_test = postgres_db.Column(CIText)

        with postgres_db.engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        postgres_db.create_all()

        view = CustomModelView(CITextModel, postgres_db.session)
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
