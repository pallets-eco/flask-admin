import typing as t

from bson import ObjectId
from bson.dbref import DBRef
from flask import Flask
from mongoengine import Document
from mongoengine import FileField
from mongoengine import StringField
from mongoengine.connection import get_db
from wtforms import fields
from wtforms import form

from flask_admin import Admin
from flask_admin.contrib.mongoengine import filters
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.contrib.mongoengine.ajax import QueryAjaxModelLoader


class Test(Document):  # type: ignore[misc]
    __test__ = False
    test1 = StringField()
    test2 = StringField()


class TestForm(form.Form):
    __test__ = False
    test1 = fields.StringField("Test1")
    test2 = fields.StringField("Test2")


class TestView(ModelView):
    __test__ = False
    column_list = ("test1", "test2", "test3", "test4")
    column_sortable_list = ("test1", "test2")

    form = TestForm

    column_filters = (
        "test1",
        filters.FilterEqual("test1", "test1"),
        filters.FilterEqual("test2", "test2"),
    )


def test_model(app: Flask, db: t.Any, admin: Admin) -> None:
    view = TestView(Test, "Test", endpoint="testview")
    admin.add_view(view)

    # Drop existing data (if any)
    db = get_db()
    for name in db.list_collection_names():
        db.drop_collection(name)

    assert view.name == "Test"
    assert view.endpoint == "testview"

    assert "test1" in view._sortable_columns
    assert "test2" in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert not view._search_supported
    assert view._filters
    for f, f_type in zip(
        view._filters,
        (
            filters.FilterLike,
            filters.FilterNotLike,
            filters.FilterEqual,
            filters.FilterNotEqual,
            filters.FilterEmpty,
            filters.FilterInList,
            filters.FilterNotInList,
            filters.FilterEqual,
            filters.FilterEqual,
        ),
        strict=True,
    ):
        assert isinstance(f, f_type)
    assert [f.__dict__ for f in view._filters[-2:]] == [
        {
            "name": "test1",
            "options": None,
            "data_type": None,
            "key_name": None,
            "column": "test1",
        },
        {
            "name": "test2",
            "options": None,
            "data_type": None,
            "key_name": None,
            "column": "test2",
        },
    ]

    # Make some test clients
    client = app.test_client()

    rv = client.get("/admin/testview/")
    assert rv.status_code == 200

    rv = client.get("/admin/testview/new/")
    assert rv.status_code == 200

    rv = client.post(
        "/admin/testview/new/", data=dict(test1="test1large", test2="test2")
    )
    assert rv.status_code == 302
    model = Test.objects.first()
    print(model)
    assert model["test1"] == "test1large"
    assert model["test2"] == "test2"

    rv = client.get("/admin/testview/")
    assert rv.status_code == 200
    assert "test1large" in rv.data.decode("utf-8")

    url = f"/admin/testview/edit/?id={model.pk}"
    rv = client.get(url)
    assert rv.status_code == 200

    rv = client.post(url, data=dict(test1="test1small", test2="test2large"))
    assert rv.status_code == 302

    print(db.test.find()[0])

    model = db.test.find()[0]
    assert model["test1"] == "test1small"
    assert model["test2"] == "test2large"

    url = "/admin/testview/delete/?id={}".format(model["_id"])
    rv = client.post(url)
    assert rv.status_code == 302
    assert db.test.estimated_document_count() == 0

    # Filter: test1 equals "test1large"
    rv = client.get("/admin/testview/?flt1_0=test1large")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1large" in data
    assert "test1small" not in data

    # Filter: test2 equals "test2"
    rv = client.get("/admin/testview/?flt2_0=test2")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2large" not in data
    assert "test2" in data


def test_query_ajax_model_loader_format_handles_dbref(db: t.Any) -> None:
    """Regression test for #2917: ``QueryAjaxModelLoader.format`` must not
    crash with ``AttributeError`` when MongoEngine cannot dereference a
    ``ReferenceField`` and returns a raw ``DBRef`` instead of a ``Document``.
    """

    class RefTarget(Document):  # type: ignore[misc]
        meta = {"collection": "ref_target"}
        name = StringField()

    loader = QueryAjaxModelLoader("ref", RefTarget, fields=["name"])

    missing_id = ObjectId()
    dbref = DBRef(collection="ref_target", id=missing_id)

    result = loader.format(dbref)

    assert result is not None
    value, label = result
    assert value == str(missing_id)
    assert "missing" in label
    assert str(missing_id) in label
def test_api_file_view_sets_content_disposition(
    app: Flask, db: t.Any, admin: Admin
) -> None:
    """Regression test for #2916: api_file_view must expose the original
    GridFS filename via Content-Disposition so browsers don't save the file
    as ``file`` with no extension.
    """

    class FileDoc(Document):  # type: ignore[misc]
        meta = {"collection": "file_doc"}
        name = StringField()
        upload = FileField()

    class FileDocView(ModelView):
        pass

    # Drop existing data
    raw_db = get_db()
    for name in raw_db.list_collection_names():
        raw_db.drop_collection(name)

    admin.add_view(FileDocView(FileDoc, "FileDoc", endpoint="filedocview"))

    doc = FileDoc(name="report")
    doc.upload.put(b"hello world", filename="report.txt", content_type="text/plain")
    doc.save()

    client = app.test_client()
    grid_id = doc.upload.grid_id
    rv = client.get(f"/admin/filedocview/api/file/?id={grid_id}&coll=fs&db=default")

    assert rv.status_code == 200
    assert rv.data == b"hello world"
    assert rv.mimetype == "text/plain"
    assert "report.txt" in rv.headers.get("Content-Disposition", "")


def test_query_ajax_model_loader_initialization(db: t.Any) -> None:
    class TestModel(Document):  # type: ignore[misc]
        meta = {"collection": "test_ajax_loader"}
        name = StringField()

    loader = QueryAjaxModelLoader("test_field", TestModel, fields=["name"])

    assert loader.name == "test_field"
    assert loader.options == {"fields": ["name"]}
