import logging

import pytest
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import Session
from wtforms import fields

from flask_admin.contrib.sqlmodel import filters
from flask_admin.tests.sqlmodel import create_models
from flask_admin.tests.sqlmodel import CustomModelView
from flask_admin.tests.sqlmodel import fill_db

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_column_editable_list(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1, db_session, column_editable_list=["test1", "enum_field"]
            )
            admin.add_view(view)

            # Test in-line editing for relations
            view = CustomModelView(Model2, db_session, column_editable_list=["model1"])
            admin.add_view(view)

            fill_db(db_session, Model1, Model2)

        client = app.test_client()

        # Test in-line edit field rendering
        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert 'data-role="x-editable"' in data

        # Form - Test basic in-line edit functionality
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1",
                "test1": "change-success-1",
            },
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully saved." == data

        # ensure the value has changed
        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "change-success-1" in data

        # Test validation error
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1",
                "enum_field": "problematic-input",
            },
        )
        assert rv.status_code == 500

        # Test invalid primary key
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1000",
                "test1": "problematic-input",
            },
        )
        data = rv.data.decode("utf-8")
        assert rv.status_code == 500

        # Test editing column not in column_editable_list
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1",
                "test2": "problematic-input",
            },
        )
        data = rv.data.decode("utf-8")
        assert "problematic-input" not in data

        rv = client.post(
            "/admin/model2/ajax/update/",
            data={
                "list_form_pk": "1",
                "model1": "3",
            },
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully saved." == data

        # confirm the value has changed
        rv = client.get("/admin/model2/")
        data = rv.data.decode("utf-8")
        assert "test1_val_3" in data


def test_column_filters(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(Model1, db_session, column_filters=["test1"])
            admin.add_view(view1)

            client = app.test_client()

            assert len(view1._filters) == 7

            # Generate views
            view2 = CustomModelView(Model2, db_session, column_filters=["model1"])

            view5 = CustomModelView(
                Model1, db_session, column_filters=["test1"], endpoint="_strings"
            )
            admin.add_view(view5)

            view6 = CustomModelView(Model2, db_session, column_filters=["int_field"])
            admin.add_view(view6)

            view7 = CustomModelView(
                Model1, db_session, column_filters=["bool_field"], endpoint="_bools"
            )
            admin.add_view(view7)

            view8 = CustomModelView(
                Model2, db_session, column_filters=["float_field"], endpoint="_float"
            )
            admin.add_view(view8)

            view9 = CustomModelView(
                Model2,
                db_session,
                endpoint="_model2",
                column_filters=["model1.bool_field"],
                column_list=[
                    "string_field",
                    "model1.id",
                    "model1.bool_field",
                ],
            )
            admin.add_view(view9)

            view10 = CustomModelView(
                Model1,
                db_session,
                column_filters=["test1"],
                endpoint="_model3",
                named_filter_urls=True,
            )
            admin.add_view(view10)

            view11 = CustomModelView(
                Model1,
                db_session,
                column_filters=["date_field", "datetime_field", "time_field"],
                endpoint="_datetime",
            )
            admin.add_view(view11)

            view12 = CustomModelView(
                Model1, db_session, column_filters=["enum_field"], endpoint="_enumfield"
            )
            admin.add_view(view12)

            view13 = CustomModelView(
                Model2,
                db_session,
                column_filters=[filters.FilterEqual(Model1.test1, "Test1")],
                endpoint="_relation_test",
            )
            admin.add_view(view13)

            view14 = CustomModelView(
                Model1,
                db_session,
                column_filters=["enum_type_field"],
                endpoint="_enumtypefield",
            )
            admin.add_view(view14)

            # Test views
            assert [
                (f["index"], f["operation"]) for f in view1._filter_groups["Test1"]
            ] == [
                (0, "contains"),
                (1, "not contains"),
                (2, "equals"),
                (3, "not equal"),
                (4, "empty"),
                (5, "in list"),
                (6, "not in list"),
            ]

            # Test filter that references property0
            assert [
                (f["index"], f["operation"])
                for f in view2._filter_groups["Model1 / Test1"]
            ] == [
                (0, "contains"),
                (1, "not contains"),
                (2, "equals"),
                (3, "not equal"),
                (4, "empty"),
                (5, "in list"),
                (6, "not in list"),
            ]

            # Test filter with a dot
            view3 = CustomModelView(
                Model2, db_session, column_filters=["model1.bool_field"]
            )

            assert [
                (f["index"], f["operation"])
                for f in view3._filter_groups["model1 / Model1 / Bool Field"]
            ] == [
                (0, "equals"),
                (1, "not equal"),
            ]

            # Test column_labels on filters
            view4 = CustomModelView(
                Model2,
                db_session,
                column_filters=["model1.bool_field", "string_field"],
                column_labels={
                    "model1.bool_field": "Test Filter #1",
                    "string_field": "Test Filter #2",
                },
            )

            assert list(view4._filter_groups.keys()) == [
                "Test Filter #1",
                "Test Filter #2",
            ]

            fill_db(db_session, Model1, Model2)

            # Test equals
            rv = client.get("/admin/model1/?flt0_0=test1_val_1")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            # the filter value is always in "data"
            # need to check a different column than test1 for the expected row

            assert "test2_val_1" in data
            assert "test1_val_2" not in data

            # Test NOT IN filter
            rv = client.get("/admin/model1/?flt0_6=test1_val_1")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")

            assert "test1_val_2" in data
            assert "test2_val_1" not in data

            # Test string filter
            assert [
                (f["index"], f["operation"]) for f in view5._filter_groups["Test1"]
            ] == [
                (0, "contains"),
                (1, "not contains"),
                (2, "equals"),
                (3, "not equal"),
                (4, "empty"),
                (5, "in list"),
                (6, "not in list"),
            ]

            # string - equals
            rv = client.get("/admin/_strings/?flt0_0=test1_val_1")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            assert "test2_val_1" in data
            assert "test1_val_2" not in data

            # Test integer filter
            assert [
                (f["index"], f["operation"]) for f in view6._filter_groups["Int Field"]
            ] == [
                (0, "equals"),
                (1, "not equal"),
                (2, "greater than"),
                (3, "smaller than"),
                (4, "empty"),
                (5, "in list"),
                (6, "not in list"),
            ]

            # integer - equals
            rv = client.get("/admin/model2/?flt0_0=5000")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            assert "test2_val_3" in data
            assert "test2_val_4" not in data

            # Test boolean filter
            assert [
                (f["index"], f["operation"]) for f in view7._filter_groups["Bool Field"]
            ] == [
                (0, "equals"),
                (1, "not equal"),
            ]

            # boolean - equals - Yes
            rv = client.get("/admin/_bools/?flt0_0=1")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            assert "test1_val_1" in data
            assert "test1_val_2" not in data

            # Test single custom filter on relation
            rv = client.get("/admin/_relation_test/?flt1_0=test1_val_1")
            data = rv.data.decode("utf-8")

            assert "test1_val_1" in data
            assert "test1_val_2" not in data


def test_column_searchable_list(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model2,
                db_session,
                column_searchable_list=["string_field", "int_field"],
            )
            admin.add_view(view)

            assert view._search_supported
            assert len(view._search_fields) == 2

            assert isinstance(view._search_fields[0][0], InstrumentedAttribute)
            assert isinstance(view._search_fields[1][0], InstrumentedAttribute)
            assert view._search_fields[0][0].key == "string_field"
            assert view._search_fields[1][0].key == "int_field"

            db_session.add(Model2(string_field="model1-test", int_field=5000))
            db_session.add(Model2(string_field="model2-test", int_field=9000))
            db_session.commit()

        client = app.test_client()

        rv = client.get("/admin/model2/?search=model1")
        data = rv.data.decode("utf-8")
        assert "model1-test" in data
        assert "model2-test" not in data

        rv = client.get("/admin/model2/?search=9000")
        data = rv.data.decode("utf-8")
        assert "model1-test" not in data
        assert "model2-test" in data


def test_column_filters_sqla_obj(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model1, db_session, column_filters=[Model1.test1])
            admin.add_view(view)

            assert len(view._filters) == 7


@pytest.mark.xfail(raises=Exception)
def test_complex_form_columns(app, engine, admin):
    with app.app_context():
        M1, M2 = create_models(engine)
        with Session(engine) as db_session:
            # test using a form column in another table
            view = CustomModelView(M2, db_session, form_columns=["model1.test1"])
            view.create_form()


def test_complex_list_columns(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            m1 = Model1(test1="model1_val1")
            db_session.add(m1)
            db_session.add(Model2(string_field="model2_val1", model1=m1))
            db_session.commit()

            # Test column_list with a list of strings on a relation
            view = CustomModelView(Model2, db_session, column_list=["model1.test1"])
            admin.add_view(view)

    client = app.test_client()

    rv = client.get("/admin/model2/")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "model1_val1" in data


def test_complex_searchable_list(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model2, db_session, column_searchable_list=["model1.test1"]
            )
            admin.add_view(view)
            view2 = CustomModelView(
                Model1,
                db_session,
                column_searchable_list=[Model2.string_field],
            )
            admin.add_view(view2)

            m1 = Model1(test1="model1-test1-val")
            m2 = Model1(test1="model1-test2-val")
            db_session.add(m1)
            db_session.add(m2)
            db_session.add(Model2(string_field="model2-test1-val", model1=m1))
            db_session.add(Model2(string_field="model2-test2-val", model1=m2))
            db_session.commit()

        client = app.test_client()

        # test relation string - 'model1.test1'
        rv = client.get("/admin/model2/?search=model1-test1")
        data = rv.data.decode("utf-8")
        assert "model2-test1-val" in data
        assert "model2-test2-val" not in data

        # test relation object - Model2.string_field
        rv = client.get("/admin/model1/?search=model2-test1")
        data = rv.data.decode("utf-8")
        assert "model1-test1-val" in data
        assert "model1-test2-val" not in data


def test_complex_searchable_list_missing_children(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                column_searchable_list=["test1", "model2.string_field"],
            )
            admin.add_view(view)

            db_session.add(Model1(test1="magic string"))
            db_session.commit()

        client = app.test_client()

        rv = client.get("/admin/model1/?search=magic")
        data = rv.data.decode("utf-8")
        assert "magic string" in data


def test_complex_sort(app, engine, admin):
    with app.app_context():
        M1, M2 = create_models(engine)
        with Session(engine) as db_session:
            m1 = M1(test1="c", test2="x")
            db_session.add(m1)
            db_session.add(M2(string_field="c", model1=m1))

            m2 = M1(test1="b", test2="x")
            db_session.add(m2)
            db_session.add(M2(string_field="b", model1=m2))

            m3 = M1(test1="a", test2="y")
            db_session.add(m3)
            db_session.add(M2(string_field="a", model1=m3))

            db_session.commit()

            # test sorting on relation string - 'model1.test1'
            view = CustomModelView(
                M2,
                db_session,
                column_list=["string_field", "model1.test1"],
                column_sortable_list=["model1.test1"],
            )
            admin.add_view(view)
            view2 = CustomModelView(
                M2,
                db_session,
                column_list=["string_field", "model1"],
                column_sortable_list=[("model1", ("model1.test2", "model1.test1"))],
                endpoint="m1_2",
            )
            admin.add_view(view2)

        client = app.test_client()

        rv = client.get("/admin/model2/?sort=0")
        assert rv.status_code == 200

        _, data = view.get_list(0, "model1.test1", False, None, None)

        assert data[0].model1.test1 == "a"
        assert data[1].model1.test1 == "b"
        assert data[2].model1.test1 == "c"

        # test sorting on multiple columns in related model
        rv = client.get("/admin/m1_2/?sort=0")
        assert rv.status_code == 200

        _, data = view2.get_list(0, "model1", False, None, None)

        assert data[0].model1.test1 == "b"
        assert data[1].model1.test1 == "c"
        assert data[2].model1.test1 == "a"


def test_default_complex_sort(app, engine, admin):
    with app.app_context():
        M1, M2 = create_models(engine)

        with Session(engine) as db_session:
            m1 = M1(test1="b")
            db_session.add(m1)
            db_session.add(M2(string_field="c", model1=m1))

            m2 = M1(test1="a")
            db_session.add(m2)
            db_session.add(M2(string_field="c", model1=m2))

            db_session.commit()

            view = CustomModelView(M2, db_session, column_default_sort="model1.test1")
            admin.add_view(view)

            _, data = view.get_list(0, None, None, None, None)

            assert len(data) == 2
            assert data[0].model1.test1 == "a"
            assert data[1].model1.test1 == "b"

            # test column_default_sort on a related table's column object
            view2 = CustomModelView(
                M2,
                db_session,
                endpoint="model2_2",
                column_default_sort=(M1.test1, False),
            )
            admin.add_view(view2)

            _, data = view2.get_list(0, None, None, None, None)

            assert len(data) == 2
            assert data[0].model1.test1 == "a"
            assert data[1].model1.test1 == "b"


def test_default_sort(app, engine, admin):
    with app.app_context():
        M1, _ = create_models(engine)

        with Session(engine) as db_session:
            db_session.add_all(
                [
                    M1(test1="c", test2="x"),
                    M1(test1="b", test2="x"),
                    M1(test1="a", test2="y"),
                ]
            )
            db_session.commit()
            count = db_session.exec(select(func.count()).select_from(M1)).scalar()
            assert count == 3

            view = CustomModelView(M1, db_session, column_default_sort="test1")
            admin.add_view(view)

            _, data = view.get_list(0, None, None, None, None)

            assert len(data) == 3
            assert data[0].test1 == "a"
            assert data[1].test1 == "b"
            assert data[2].test1 == "c"

            # test default sort on renamed columns - with column_list scaffolding
            view2 = CustomModelView(
                M1,
                db_session,
                column_default_sort="test1",
                column_labels={"test1": "blah"},
                endpoint="m1_2",
            )
            admin.add_view(view2)

            _, data = view2.get_list(0, None, None, None, None)

            assert len(data) == 3
            assert data[0].test1 == "a"
            assert data[1].test1 == "b"
            assert data[2].test1 == "c"

            # test default sort on renamed columns - without column_list scaffolding
            view3 = CustomModelView(
                M1,
                db_session,
                column_default_sort="test1",
                column_labels={"test1": "blah"},
                endpoint="m1_3",
                column_list=["test1"],
            )
            admin.add_view(view3)

            _, data = view3.get_list(0, None, None, None, None)

            assert len(data) == 3
            assert data[0].test1 == "a"
            assert data[1].test1 == "b"
            assert data[2].test1 == "c"

            # test default sort with multiple columns
            order = [("test2", False), ("test1", False)]
            view4 = CustomModelView(
                M1, db_session, column_default_sort=order, endpoint="m1_4"
            )
            admin.add_view(view4)

            _, data = view4.get_list(0, None, None, None, None)

            assert len(data) == 3
            assert data[0].test1 == "b"
            assert data[1].test1 == "c"
            assert data[2].test1 == "a"


def test_details_view(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view_no_details = CustomModelView(Model1, db_session)
            admin.add_view(view_no_details)

            # fields are scaffolded
            view_w_details = CustomModelView(Model2, db_session, can_view_details=True)
            admin.add_view(view_w_details)

            # show only specific fields in details w/ column_details_list
            string_field_view = CustomModelView(
                Model2,
                db_session,
                can_view_details=True,
                column_details_list=["string_field"],
                endpoint="sf_view",
            )
            admin.add_view(string_field_view)

            fill_db(db_session, Model1, Model2)

        client = app.test_client()

        # ensure link to details is hidden when can_view_details is disabled
        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "/admin/model1/details/" not in data

        # ensure link to details view appears
        rv = client.get("/admin/model2/")
        data = rv.data.decode("utf-8")
        assert "/admin/model2/details/" in data

        # test redirection when details are disabled
        rv = client.get("/admin/model1/details/?url=%2Fadmin%2Fmodel1%2F&id=1")
        assert rv.status_code == 302

        # test if correct data appears in details view when enabled
        rv = client.get("/admin/model2/details/?url=%2Fadmin%2Fmodel2%2F&id=1")
        data = rv.data.decode("utf-8")
        assert "String Field" in data
        assert "test2_val_1" in data
        assert "test1_val_1" in data

        # test column_details_list
        rv = client.get("/admin/sf_view/details/?url=%2Fadmin%2Fsf_view%2F&id=1")
        data = rv.data.decode("utf-8")
        assert "String Field" in data
        assert "test2_val_1" in data
        assert "test1_val_1" not in data


def test_exclude_columns(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                column_exclude_list=[
                    "test2",
                    "test4",
                    "enum_field",
                    "enum_type_field",
                    "date_field",
                    "datetime_field",
                    "time_field",
                    "sqla_utils_choice",
                    "sqla_utils_enum",
                    "sqla_utils_arrow",
                    "sqla_utils_uuid",
                    "sqla_utils_url",
                    "sqla_utils_ip_address",
                    "sqla_utils_currency",
                    "sqla_utils_color",
                    "model2",
                ],
            )
            admin.add_view(view)

        assert view._list_columns == [
            ("id", "Id"),
            ("test1", "Test1"),
            ("test3", "Test3"),
            ("bool_field", "Bool Field"),
            ("email_field", "Email Field"),
            ("choice_field", "Choice Field"),
        ]

        client = app.test_client()

        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "Test1" in data


def test_extra_args_filter(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view2 = CustomModelView(
                Model2,
                db_session,
                column_filters=["int_field"],
            )
            admin.add_view(view2)

            db_session.add(Model2(string_field="model2-test", int_field=5000))
            db_session.commit()

        client = app.test_client()

        # Check that extra args in the url are propagated as hidden fields in the form
        rv = client.get("/admin/model2/?flt1_0=5000&foo=bar")
        data = rv.data.decode("utf-8")
        assert '<input type="hidden" name="foo" value="bar">' in data


def test_extra_args_search(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(
                Model1,
                db_session,
                column_searchable_list=["test1"],
            )
            admin.add_view(view1)

            db_session.add(Model2(string_field="model1-test"))
            db_session.commit()

        client = app.test_client()

        # Check that extra args in the url are propagated as hidden fields
        # in the search form
        rv = client.get("/admin/model1/?search=model1&foo=bar")
        data = rv.data.decode("utf-8")
        assert '<input type="hidden" name="foo" value="bar">' in data


def test_extra_fields(app, engine, admin):
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                form_extra_fields={"extra_field": fields.StringField("Extra Field")},
            )
            admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        # Check presence and order
        data = rv.data.decode("utf-8")
        assert "Extra Field" in data
        pos1 = data.find("Extra Field")
        pos2 = data.find("Test1")
        assert pos2 < pos1


def test_list_columns(app, engine, admin):
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            # Test column_list with a list of strings
            view = CustomModelView(
                Model1,
                db_session,
                column_list=["test1", "test3"],
                column_labels=dict(test1="Column1"),
            )
            admin.add_view(view)
            # Test column_list with a list of SQLAlchemy columns
            view2 = CustomModelView(
                Model1,
                db_session,
                endpoint="model1_2",
                column_list=[Model1.test1, Model1.test3],
                column_labels=dict(test1="Column1"),
            )
            admin.add_view(view2)

        assert len(view._list_columns) == 2
        assert view._list_columns == [("test1", "Column1"), ("test3", "Test3")]

        client = app.test_client()

        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "Column1" in data
        assert "Test2" not in data

        assert len(view2._list_columns) == 2
        assert view2._list_columns == [("test1", "Column1"), ("test3", "Test3")]

        rv = client.get("/admin/model1_2/")
        data = rv.data.decode("utf-8")
        assert "Column1" in data
        assert "Test2" not in data


def test_on_model_change_delete(app, engine, admin):
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:

            class ModelView(CustomModelView):
                def on_model_change(self, form, model, is_created):
                    model.test1 = model.test1.upper()

                def update_model(self, form, model):
                    # Modify the form data before it's applied to the model
                    if hasattr(form, "test1") and form.test1.data:
                        form.test1.data = form.test1.data.upper()

                    return super().update_model(form, model)

                def delete_model(self, model):
                    # Call your hook before deleting
                    self.on_model_delete(model)

                    # Then call the parent's delete_model
                    return super().delete_model(model)

                def on_model_delete(self, model):
                    self.deleted = True

            view = ModelView(Model1, db_session)
            admin.add_view(view)

            client = app.test_client()
            client.post(
                "/admin/model1/new/", data=dict(test1="test1large", test2="test2")
            )

            model = db_session.exec(select(Model1)).scalars().first()
            assert model.test1 == "TEST1LARGE"
            db_session.refresh(model)

            url = f"/admin/model1/edit/?id={model.id}"
            resp = client.post(url, data=dict(test1="test1small", test2="test2large"))
            assert resp.status_code == 302

            db_session.expire_all()
            model = db_session.exec(select(Model1)).scalars().first()
            assert model.test1 == "TEST1SMALL"

            url = f"/admin/model1/delete/?id={model.id}"
            client.post(url)
            assert view.deleted


def test_multiple_delete(app, engine, admin):
    with app.app_context():
        M1, _ = create_models(engine)
        with Session(engine) as db_session:
            db_session.add_all([M1(test1="a"), M1(test1="b"), M1(test1="c")])
            db_session.commit()
            assert len(db_session.exec(select(M1)).scalars().all()) == 3

            view = CustomModelView(M1, db_session)
            admin.add_view(view)

            client = app.test_client()

            rv = client.post(
                "/admin/model1/action/", data=dict(action="delete", rowid=[1, 2, 3])
            )
            assert rv.status_code == 302
            assert len(db_session.exec(select(M1)).scalars().all()) == 0


def test_url_args(app, engine, admin):
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                page_size=2,
                column_searchable_list=["test1"],
                column_filters=["test1"],
            )
            admin.add_view(view)

            db_session.add(Model1(test1="data1"))
            db_session.add(Model1(test1="data2"))
            db_session.add(Model1(test1="data3"))
            db_session.add(Model1(test1="data4"))
            db_session.commit()

            client = app.test_client()

            rv = client.get("/admin/model1/")
            data = rv.data.decode("utf-8")
            assert "data1" in data
            assert "data3" not in data

            # page
            rv = client.get("/admin/model1/?page=1")
            data = rv.data.decode("utf-8")
            assert "data1" not in data
            assert "data3" in data

            # sort
            rv = client.get("/admin/model1/?sort=0&desc=1")
            data = rv.data.decode("utf-8")
            assert "data1" not in data
            assert "data3" in data
            assert "data4" in data

            # search
            rv = client.get("/admin/model1/?search=data1")
            data = rv.data.decode("utf-8")
            assert "data1" in data
            assert "data2" not in data

            rv = client.get("/admin/model1/?search=^data1")
            data = rv.data.decode("utf-8")
            assert "data2" not in data

            # like
            rv = client.get("/admin/model1/?flt0=0&flt0v=data1")
            data = rv.data.decode("utf-8")
            assert "data1" in data

            # not like
            rv = client.get("/admin/model1/?flt0=1&flt0v=data1")
            data = rv.data.decode("utf-8")
            assert "data2" in data
