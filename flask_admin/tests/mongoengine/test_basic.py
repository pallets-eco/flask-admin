from datetime import datetime

import pytest
from mongoengine import Document
from mongoengine import StringField
from mongoengine.connection import get_db
from wtforms import fields
from wtforms import form

from flask_admin.contrib.mongoengine import filters
from flask_admin.contrib.mongoengine import ModelView


class Test(Document):
    __test__ = False
    test1 = StringField()
    test2 = StringField()


class TestForm(form.Form):
    __test__ = False
    test1 = fields.StringField("Test1")
    test2 = fields.StringField("Test2")

    intfield = fields.IntegerField("intfield")
    floatfield = fields.FloatField("floatfield")
    boolfield = fields.BooleanField("boolfield")
    datefield = fields.DateField("datefield")


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
    assert all(isinstance(f, filters.FilterEqual) for f in view._filters)
    assert [f.__dict__ for f in view._filters] == [
        {
            "name": "test1",
            "options": None,
            "data_type": None,
            "key_name": None,
            "url_value": None,
            "column": "test1",
        },
        {
            "name": "test2",
            "options": None,
            "data_type": None,
            "key_name": None,
            "url_value": None,
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


def create_filter_params():
    params = [
        (filters.FilterEqual, "test1", "x", "flt0_0", "flt0_test1_equals", "x"),
        (filters.FilterNotEqual, "test1", "x", "flt0_0", "flt0_test1_not_equal", "x"),
        (filters.FilterLike, "test1", "x", "flt0_0", "flt0_test1_contains", "x"),
        (filters.FilterNotLike, "test1", "x", "flt0_0", "flt0_test1_not_contains", "x"),
        (filters.FilterGreater, "test1", "x", "flt0_0", "flt0_test1_greater_than", "x"),
        (filters.FilterSmaller, "test1", "x", "flt0_0", "flt0_test1_smaller_than", "x"),
        (filters.FilterEmpty, "test1", "1", "flt0_0", "flt0_test1_empty", "1"),
        (
            filters.FilterInList,
            "test1",
            ["x", "y"],
            "flt0_0",
            "flt0_test1_in_list",
            "x,y",
        ),
        (
            filters.FilterNotInList,
            "test1",
            ["x", "y"],
            "flt0_0",
            "flt0_test1_not_in_list",
            "x,y",
        ),
        (
            filters.BooleanEqualFilter,
            "boolfield",
            "1",
            "flt0_0",
            "flt0_boolfield_equals",
            "1",
        ),
        (
            filters.BooleanNotEqualFilter,
            "boolfield",
            "1",
            "flt0_0",
            "flt0_boolfield_not_equal",
            "1",
        ),
        (
            filters.IntEqualFilter,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_equals",
            "10",
        ),
        (
            filters.IntNotEqualFilter,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_not_equal",
            "10",
        ),
        (
            filters.IntGreaterFilter,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_greater_than",
            "10",
        ),
        (
            filters.IntSmallerFilter,
            "intfield",
            10,
            "flt0_0",
            "flt0_intfield_smaller_than",
            "10",
        ),
        (
            filters.IntInListFilter,
            "intfield",
            [10, 20],
            "flt0_0",
            "flt0_intfield_in_list",
            "10,20",
        ),
        (
            filters.IntNotInListFilter,
            "intfield",
            [10, 20],
            "flt0_0",
            "flt0_intfield_not_in_list",
            "10,20",
        ),
        (
            filters.FloatEqualFilter,
            "floatfield",
            1.2,
            "flt0_0",
            "flt0_floatfield_equals",
            "1.2",
        ),
        (
            filters.FloatNotEqualFilter,
            "floatfield",
            1.2,
            "flt0_0",
            "flt0_floatfield_not_equal",
            "1.2",
        ),
        (
            filters.FloatGreaterFilter,
            "floatfield",
            1.2,
            "flt0_0",
            "flt0_floatfield_greater_than",
            "1.2",
        ),
        (
            filters.FloatSmallerFilter,
            "floatfield",
            1.2,
            "flt0_0",
            "flt0_floatfield_smaller_than",
            "1.2",
        ),
        (
            filters.FloatInListFilter,
            "floatfield",
            [1.2, 2.4],
            "flt0_0",
            "flt0_floatfield_in_list",
            "1.2,2.4",
        ),
        (
            filters.FloatNotInListFilter,
            "floatfield",
            [1.2, 2.4],
            "flt0_0",
            "flt0_floatfield_not_in_list",
            "1.2,2.4",
        ),
        (
            filters.DateTimeEqualFilter,
            "datefield",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_datefield_equals",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeNotEqualFilter,
            "datefield",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_datefield_not_equal",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeGreaterFilter,
            "datefield",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_datefield_greater_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeSmallerFilter,
            "datefield",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_datefield_smaller_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeBetweenFilter,
            "datefield",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_0",
            "flt0_datefield_between",
            "2025-11-01+00:00:00+to+2025-11-15+00:00:00",
        ),
        (
            filters.DateTimeNotBetweenFilter,
            "datefield",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_0",
            "flt0_datefield_not_between",
            "2025-11-01+00:00:00+to+2025-11-15+00:00:00",
        ),
    ]
    return params


@pytest.mark.parametrize(
    "FilterClass, col, filter_value, arg_key, arg_named_key, expected_value",
    create_filter_params(),
)
def test_url_for(
    app,
    app_context,
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

    view = MyView(Test, "Test", endpoint="user")
    admin.add_view(view)

    d1 = filter_value
    filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
    assert filtered_url == f"/admin/user/?{arg_key}={expected_value}"

    view.named_filter_urls = True
    d1 = filter_value
    filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
    assert filtered_url == f"/admin/user/?{arg_named_key}={expected_value}"
