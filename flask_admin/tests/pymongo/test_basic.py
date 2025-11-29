import pytest
from wtforms import fields
from wtforms import form

from flask_admin.contrib.pymongo import filters
from flask_admin.contrib.pymongo import ModelView


class TestForm(form.Form):
    __test__ = False
    test1 = fields.StringField("Test1")
    test2 = fields.StringField("Test2")

    int_field = fields.IntegerField("int_field")
    bool_field = fields.BooleanField("bool_field")


class TestView(ModelView):
    __test__ = False
    column_list = ("test1", "int_field", "bool_field", "test4")
    column_sortable_list = ("test1", "test2", "int_field")

    form = TestForm


def test_model(app, db, admin):
    view = TestView(db.test, "Test")
    admin.add_view(view)

    # Drop existing data (if any)
    db.test.delete_many({})

    assert view.name == "Test"
    assert view.endpoint == "testview"

    assert "test1" in view._sortable_columns
    assert "test2" in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert not view._search_supported
    assert view._filters is None

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

    model = db.test.find()[0]
    print(model)
    assert model["test1"] == "test1large"
    assert model["test2"] == "test2"

    rv = client.get("/admin/testview/")
    assert rv.status_code == 200
    assert "test1large" in rv.data.decode("utf-8")

    url = "/admin/testview/edit/?id={}".format(model["_id"])
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


def create_filter_params():
    params = [
        (filters.FilterEqual, "test1", "x", "flt0_0", "flt0_test1_equals", "x"),
        (filters.FilterNotEqual, "test1", "x", "flt0_0", "flt0_test1_not_equal", "x"),
        (filters.FilterLike, "test1", "x", "flt0_0", "flt0_test1_contains", "x"),
        (filters.FilterNotLike, "test1", "x", "flt0_0", "flt0_test1_not_contains", "x"),
        (
            filters.FilterGreater,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_greater_than",
            "10",
        ),
        (
            filters.FilterSmaller,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_smaller_than",
            "10",
        ),
        (
            filters.BooleanEqualFilter,
            "boolfield",
            True,
            "flt0_0",
            "flt0_boolfield_equals",
            "1",
        ),  # equals
        (
            filters.BooleanNotEqualFilter,
            "boolfield",
            True,
            "flt0_0",
            "flt0_boolfield_not_equal",
            "1",
        ),  # not equal
    ]
    return params


@pytest.mark.parametrize(
    "FilterClass, col, filter_value, arg_key, arg_named_key, expected_value",
    create_filter_params(),
)
def test_url_for(
    app,
    db,
    admin,
    FilterClass,
    col,
    filter_value,
    arg_key,
    arg_named_key,
    expected_value,
):
    class MyView(ModelView):
        __test__ = False

        column_list = ("test1", "test2", "test3", "test4")
        column_sortable_list = ("test1", "test2")
        column_filters = [
            FilterClass(col, col),
        ]
        form = TestForm

    view = MyView(db.test, endpoint="user")
    admin.add_view(view)

    # print(view.column_filters)

    d1 = filter_value
    filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
    assert filtered_url == f"/admin/user/?{arg_key}={expected_value}"

    view.named_filter_urls = True
    d1 = filter_value
    filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
    assert filtered_url == f"/admin/user/?{arg_named_key}={expected_value}"
