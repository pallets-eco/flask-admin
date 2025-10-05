from mongoengine import Document
from mongoengine import StringField
from mongoengine.connection import get_db
from wtforms import fields
from wtforms import form

from flask_admin.contrib.mongoengine import filters
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.contrib.mongoengine.filters import FilterEqual


class Test(Document):
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
        filters.FilterEqual("test1", "test1"),
        filters.FilterEqual("test2", "test2"),
    )


def test_model(app, db, admin):
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
    assert all(isinstance(f, FilterEqual) for f in view._filters)
    assert [f.__dict__ for f in view._filters] == [
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
