from mongoengine import Document
from mongoengine import ReferenceField
from mongoengine import StringField
from mongoengine.connection import get_db
from wtforms import fields
from wtforms import form

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


def test_query_ajax_model_loader_initialization(db):
    class TestModel(Document):  # type: ignore[misc]
        meta = {"collection": "test_ajax_loader"}
        name = StringField()

    loader = QueryAjaxModelLoader("test_field", TestModel, fields=["name"])

    assert loader.name == "test_field"
    assert loader.options == {"fields": ["name"]}


def test_column_editable_list(app, db, admin):
    class EditableModel(Document):  # type: ignore[misc]
        meta = {"collection": "editable_test"}
        test1 = StringField(max_length=20)
        test2 = StringField()

    class RelatedModel(Document):  # type: ignore[misc]
        meta = {"collection": "editable_related_test"}
        name = StringField()
        ref = ReferenceField(EditableModel)

        def __str__(self):
            return self.name or ""

    # Drop existing data
    mongo_db = get_db()
    for name in ("editable_test", "editable_related_test"):
        mongo_db.drop_collection(name)

    view = ModelView(
        EditableModel,
        "EditableModel",
        column_editable_list=["test1"],
        endpoint="editable_model",
    )
    admin.add_view(view)

    view2 = ModelView(
        RelatedModel,
        "RelatedModel",
        column_editable_list=["ref"],
        endpoint="editable_related",
    )
    admin.add_view(view2)

    # Seed data
    obj1 = EditableModel(test1="val1", test2="val2").save()
    obj2 = EditableModel(test1="val2", test2="val3").save()
    RelatedModel(name="related1", ref=obj1).save()

    client = app.test_client()

    # Test in-line edit field rendering
    rv = client.get("/admin/editable_model/")
    data = rv.data.decode("utf-8")
    assert "hx-get=" in data
    assert 'class="editable-cell"' in data

    # Test basic in-line edit functionality
    rv = client.post(
        "/admin/editable_model/ajax/update/",
        data={
            "list_form_pk": str(obj1.pk),
            "test1": "change-success-1",
        },
    )
    data = rv.data.decode("utf-8")
    assert "change-success-1" in data
    assert 'class="editable-cell"' in data

    # Ensure the value has changed
    rv = client.get("/admin/editable_model/")
    data = rv.data.decode("utf-8")
    assert "change-success-1" in data

    # Test editing column not in column_editable_list
    rv = client.post(
        "/admin/editable_model/ajax/update/",
        data={
            "list_form_pk": str(obj1.pk),
            "test2": "problematic-input",
        },
    )
    assert rv.status_code == 404

    # Test ajax_edit endpoint
    rv = client.get(f"/admin/editable_model/ajax/edit/?pk={obj1.pk}&field=test1")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert 'hx-post="./ajax/update/"' in data
    assert 'name="test1"' in data

    # Test ajax_edit for non-editable field
    rv = client.get(f"/admin/editable_model/ajax/edit/?pk={obj1.pk}&field=test2")
    assert rv.status_code == 404

    # Test relation editing
    rv = client.post(
        "/admin/editable_related/ajax/update/",
        data={
            "list_form_pk": str(RelatedModel.objects.first().pk),
            "ref": str(obj2.pk),
        },
    )
    data = rv.data.decode("utf-8")
    assert 'class="editable-cell"' in data
