from datetime import date
from datetime import datetime
from datetime import time

import peewee
from wtforms import fields
from wtforms import validators

from flask_admin import form
from flask_admin._compat import as_unicode
from flask_admin._compat import iteritems
from flask_admin.contrib.peewee import ModelView


class CustomModelView(ModelView):
    def __init__(
        self, model, name=None, category=None, endpoint=None, url=None, **kwargs
    ):
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super().__init__(model, name, category, endpoint, url)


def create_models(db):
    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model1(BaseModel):
        def __init__(
            self,
            test1=None,
            test2=None,
            test3=None,
            test4=None,
            date_field=None,
            timeonly_field=None,
            datetime_field=None,
            **kwargs,
        ):
            super().__init__(**kwargs)

            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4
            self.date_field = date_field
            self.timeonly_field = timeonly_field
            self.datetime_field = datetime_field

        test1 = peewee.CharField(max_length=20, null=True)
        test2 = peewee.CharField(max_length=20, null=True)
        test3 = peewee.TextField(null=True)
        test4 = peewee.TextField(null=True)
        date_field = peewee.DateField(null=True)
        timeonly_field = peewee.TimeField(null=True)
        datetime_field = peewee.DateTimeField(null=True)

        def __str__(self):
            # "or ''" fixes error when loading choices for relation field:
            # TypeError: coercing to Unicode: need string or buffer, NoneType found
            return self.test1 or ""

    class Model2(BaseModel):
        def __init__(
            self,
            char_field=None,
            int_field=None,
            float_field=None,
            bool_field=0,
            **kwargs,
        ):
            super().__init__(**kwargs)

            self.char_field = char_field
            self.int_field = int_field
            self.float_field = float_field
            self.bool_field = bool_field

        char_field = peewee.CharField(max_length=20)
        int_field = peewee.IntegerField(null=True)
        float_field = peewee.FloatField(null=True)
        bool_field = peewee.BooleanField()

        # Relation
        model1 = peewee.ForeignKeyField(Model1, null=True)

    Model1.create_table()
    Model2.create_table()

    return Model1, Model2


def fill_db(Model1, Model2):
    Model1("test1_val_1", "test2_val_1").save()
    Model1("test1_val_2", "test2_val_2").save()
    Model1("test1_val_3", "test2_val_3").save()
    Model1("test1_val_4", "test2_val_4").save()
    Model1(None, "empty_obj").save()

    Model2("char_field_val_1", None, None, bool_field=True).save()
    Model2("char_field_val_2", None, None, bool_field=False).save()
    Model2("char_field_val_3", 5000, 25.9).save()
    Model2("char_field_val_4", 9000, 75.5).save()
    Model2("char_field_val_5", 6169453081680413441).save()

    Model1("date_obj1", date_field=date(2014, 11, 17)).save()
    Model1("date_obj2", date_field=date(2013, 10, 16)).save()
    Model1("timeonly_obj1", timeonly_field=time(11, 10, 9)).save()
    Model1("timeonly_obj2", timeonly_field=time(10, 9, 8)).save()
    Model1("datetime_obj1", datetime_field=datetime(2014, 4, 3, 1, 9, 0)).save()
    Model1("datetime_obj2", datetime_field=datetime(2013, 3, 2, 0, 8, 0)).save()


def test_model(app, db, admin):
    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1)
    admin.add_view(view)

    assert view.model == Model1
    assert view.name == "Model1"
    assert view.endpoint == "model1"

    assert view._primary_key == "id"

    assert "test1" in view._sortable_columns
    assert "test2" in view._sortable_columns
    assert "test3" in view._sortable_columns
    assert "test4" in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert not view._search_supported
    assert view._filters is None

    # Verify form
    assert view._create_form_class.test1.field_class == fields.StringField
    assert view._create_form_class.test2.field_class == fields.StringField
    assert view._create_form_class.test3.field_class == fields.TextAreaField
    assert view._create_form_class.test4.field_class == fields.TextAreaField

    # Make some test clients
    client = app.test_client()

    rv = client.get("/admin/model1/")
    assert rv.status_code == 200

    rv = client.get("/admin/model1/new/")
    assert rv.status_code == 200

    rv = client.post("/admin/model1/new/", data=dict(test1="test1large", test2="test2"))
    assert rv.status_code == 302

    model = Model1.select().get()
    assert model.test1 == "test1large"
    assert model.test2 == "test2"
    assert model.test3 is None or model.test3 == ""
    assert model.test4 is None or model.test4 == ""

    rv = client.get("/admin/model1/")
    assert rv.status_code == 200
    assert b"test1large" in rv.data

    url = f"/admin/model1/edit/?id={model.id}"
    rv = client.get(url)
    assert rv.status_code == 200

    rv = client.post(url, data=dict(test1="test1small", test2="test2large"))
    assert rv.status_code == 302

    model = Model1.select().get()
    assert model.test1 == "test1small"
    assert model.test2 == "test2large"
    assert model.test3 is None or model.test3 == ""
    assert model.test4 is None or model.test4 == ""

    url = f"/admin/model1/delete/?id={model.id}"
    rv = client.post(url)
    assert rv.status_code == 302
    assert Model1.select().count() == 0


def test_column_editable_list(app, db, admin):
    Model1, Model2 = create_models(db)

    # wtf-peewee doesn't automatically add length validators for max_length
    form_args = {"test1": {"validators": [validators.Length(max=20)]}}
    view = CustomModelView(Model1, column_editable_list=["test1"], form_args=form_args)
    admin.add_view(view)

    # Test in-line editing for relations
    view = CustomModelView(Model2, column_editable_list=["model1"])
    admin.add_view(view)

    fill_db(Model1, Model2)

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
            "test1": (
                "longerthantwentycharacterslongerthantwentycharacterslonger"
                "thantwentycharacterslongerthantwentycharacters"
            ),
        },
    )
    data = rv.data.decode("utf-8")
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


def test_details_view(app, db, admin):
    Model1, Model2 = create_models(db)

    view_no_details = CustomModelView(Model1)
    admin.add_view(view_no_details)

    # fields are scaffolded
    view_w_details = CustomModelView(Model2, can_view_details=True)
    admin.add_view(view_w_details)

    # show only specific fields in details w/ column_details_list
    char_field_view = CustomModelView(
        Model2,
        can_view_details=True,
        column_details_list=["char_field"],
        endpoint="cf_view",
    )
    admin.add_view(char_field_view)

    fill_db(Model1, Model2)

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
    rv = client.get("/admin/model1/details/?url=%2Fadmin%2Fmodel1%2F&id=3")
    assert rv.status_code == 302

    # test if correct data appears in details view when enabled
    rv = client.get("/admin/model2/details/?url=%2Fadmin%2Fmodel2%2F&id=3")
    data = rv.data.decode("utf-8")
    assert "Char Field" in data
    assert "char_field_val_3" in data
    assert "Int Field" in data
    assert "5000" in data

    # test column_details_list
    rv = client.get("/admin/cf_view/details/?url=%2Fadmin%2Fcf_view%2F&id=3")
    data = rv.data.decode("utf-8")
    assert "Char Field" in data
    assert "char_field_val_3" in data
    assert "Int Field" not in data
    assert "5000" not in data


def test_column_filters(app, db, admin):
    Model1, Model2 = create_models(db)

    fill_db(Model1, Model2)

    # Test string filter
    view = CustomModelView(Model1, column_filters=["test1"])
    admin.add_view(view)

    # Test int filter
    view2 = CustomModelView(Model2, column_filters=["int_field"])
    admin.add_view(view2)

    # Test boolean filter
    view3 = CustomModelView(Model2, column_filters=["bool_field"], endpoint="_bools")
    admin.add_view(view3)

    # Test float filter
    view4 = CustomModelView(Model2, column_filters=["float_field"], endpoint="_float")
    admin.add_view(view4)

    # Test date, time, and datetime filters
    view5 = CustomModelView(
        Model1,
        column_filters=["date_field", "datetime_field", "timeonly_field"],
        endpoint="_datetime",
    )
    admin.add_view(view5)

    assert len(view._filters) == 7

    assert [(f["index"], f["operation"]) for f in view._filter_groups["Test1"]] == [
        (0, "contains"),
        (1, "not contains"),
        (2, "equals"),
        (3, "not equal"),
        (4, "empty"),
        (5, "in list"),
        (6, "not in list"),
    ]

    # Make some test clients
    client = app.test_client()

    # string - equals
    rv = client.get("/admin/model1/?flt0_0=test1_val_1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" in data
    assert "test1_val_2" not in data

    # string - not equal
    rv = client.get("/admin/model1/?flt0_1=test1_val_1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" not in data
    assert "test1_val_2" in data

    # string - contains
    rv = client.get("/admin/model1/?flt0_2=test1_val_1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" in data
    assert "test1_val_2" not in data

    # string - not contains
    rv = client.get("/admin/model1/?flt0_3=test1_val_1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" not in data
    assert "test1_val_2" in data

    # string - empty
    rv = client.get("/admin/model1/?flt0_4=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "empty_obj" in data
    assert "test1_val_1" not in data
    assert "test1_val_2" not in data

    # string - not empty
    rv = client.get("/admin/model1/?flt0_4=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "empty_obj" not in data
    assert "test1_val_1" in data
    assert "test1_val_2" in data

    # string - in list
    rv = client.get("/admin/model1/?flt0_5=test1_val_1%2Ctest1_val_2")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" in data
    assert "test2_val_2" in data
    assert "test1_val_3" not in data
    assert "test1_val_4" not in data

    # string - not in list
    rv = client.get("/admin/model1/?flt0_6=test1_val_1%2Ctest1_val_2")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test2_val_1" not in data
    assert "test2_val_2" not in data
    assert "test1_val_3" in data
    assert "test1_val_4" in data

    assert [
        (f["index"], f["operation"]) for f in view2._filter_groups["Int Field"]
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
    assert "char_field_val_3" in data
    assert "char_field_val_4" not in data

    # integer - equals (huge number)
    rv = client.get("/admin/model2/?flt0_0=6169453081680413441")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_5" in data
    assert "char_field_val_4" not in data

    # integer - equals - test validation
    rv = client.get("/admin/model2/?flt0_0=badval")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "Invalid Filter Value" in data

    # integer - not equal
    rv = client.get("/admin/model2/?flt0_1=5000")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" not in data
    assert "char_field_val_4" in data

    # integer - greater
    rv = client.get("/admin/model2/?flt0_2=6000")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" not in data
    assert "char_field_val_4" in data

    # integer - smaller
    rv = client.get("/admin/model2/?flt0_3=6000")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" in data
    assert "char_field_val_4" not in data

    # integer - empty
    rv = client.get("/admin/model2/?flt0_4=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" not in data
    assert "char_field_val_4" not in data

    # integer - not empty
    rv = client.get("/admin/model2/?flt0_4=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" in data
    assert "char_field_val_4" in data

    # integer - in list
    rv = client.get("/admin/model2/?flt0_5=5000%2C9000")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" in data
    assert "char_field_val_4" in data

    # integer - in list (huge number)
    rv = client.get("/admin/model2/?flt0_5=6169453081680413441")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_5" in data

    # integer - in list - test validation
    rv = client.get("/admin/model2/?flt0_5=5000%2Cbadval")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "Invalid Filter Value" in data

    # integer - not in list
    rv = client.get("/admin/model2/?flt0_6=5000%2C9000")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" not in data
    assert "char_field_val_4" not in data

    assert [
        (f["index"], f["operation"]) for f in view3._filter_groups["Bool Field"]
    ] == [
        (0, "equals"),
        (1, "not equal"),
    ]

    # boolean - equals - Yes
    rv = client.get("/admin/_bools/?flt0_0=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" not in data

    # boolean - equals - No
    rv = client.get("/admin/_bools/?flt0_0=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" in data

    # boolean - not equals - Yes
    rv = client.get("/admin/_bools/?flt0_1=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" in data

    # boolean - not equals - No
    rv = client.get("/admin/_bools/?flt0_1=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" not in data

    assert [
        (f["index"], f["operation"]) for f in view4._filter_groups["Float Field"]
    ] == [
        (0, "equals"),
        (1, "not equal"),
        (2, "greater than"),
        (3, "smaller than"),
        (4, "empty"),
        (5, "in list"),
        (6, "not in list"),
    ]

    # float - equals
    rv = client.get("/admin/_float/?flt0_0=25.9")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" in data
    assert "char_field_val_4" not in data

    # float - equals - test validation
    rv = client.get("/admin/_float/?flt0_0=badval")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "Invalid Filter Value" in data

    # float - not equal
    rv = client.get("/admin/_float/?flt0_1=25.9")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" not in data
    assert "char_field_val_4" in data

    # float - greater
    rv = client.get("/admin/_float/?flt0_2=60.5")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" not in data
    assert "char_field_val_4" in data

    # float - smaller
    rv = client.get("/admin/_float/?flt0_3=60.5")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_3" in data
    assert "char_field_val_4" not in data

    # float - empty
    rv = client.get("/admin/_float/?flt0_4=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" not in data
    assert "char_field_val_4" not in data

    # float - not empty
    rv = client.get("/admin/_float/?flt0_4=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" in data
    assert "char_field_val_4" in data

    # float - in list
    rv = client.get("/admin/_float/?flt0_5=25.9%2C75.5")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" not in data
    assert "char_field_val_2" not in data
    assert "char_field_val_3" in data
    assert "char_field_val_4" in data

    # float - in list - test validation
    rv = client.get("/admin/_float/?flt0_5=25.9%2Cbadval")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "Invalid Filter Value" in data

    # float - not in list
    rv = client.get("/admin/_float/?flt0_6=25.9%2C75.5")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "char_field_val_1" in data
    assert "char_field_val_2" in data
    assert "char_field_val_3" not in data
    assert "char_field_val_4" not in data

    assert [
        (f["index"], f["operation"]) for f in view5._filter_groups["Date Field"]
    ] == [
        (0, "equals"),
        (1, "not equal"),
        (2, "greater than"),
        (3, "smaller than"),
        (4, "between"),
        (5, "not between"),
        (6, "empty"),
    ]

    assert [
        (f["index"], f["operation"]) for f in view5._filter_groups["Datetime Field"]
    ] == [
        (7, "equals"),
        (8, "not equal"),
        (9, "greater than"),
        (10, "smaller than"),
        (11, "between"),
        (12, "not between"),
        (13, "empty"),
    ]

    assert [
        (f["index"], f["operation"]) for f in view5._filter_groups["Timeonly Field"]
    ] == [
        (14, "equals"),
        (15, "not equal"),
        (16, "greater than"),
        (17, "smaller than"),
        (18, "between"),
        (19, "not between"),
        (20, "empty"),
    ]

    # date - equals
    rv = client.get("/admin/_datetime/?flt0_0=2014-11-17")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" in data
    assert "date_obj2" not in data

    # date - not equal
    rv = client.get("/admin/_datetime/?flt0_1=2014-11-17")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" not in data
    assert "date_obj2" in data

    # date - greater
    rv = client.get("/admin/_datetime/?flt0_2=2014-11-16")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" in data
    assert "date_obj2" not in data

    # date - smaller
    rv = client.get("/admin/_datetime/?flt0_3=2014-11-16")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" not in data
    assert "date_obj2" in data

    # date - between
    rv = client.get("/admin/_datetime/?flt0_4=2014-11-13+to+2014-11-20")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" in data
    assert "date_obj2" not in data

    # date - not between
    rv = client.get("/admin/_datetime/?flt0_5=2014-11-13+to+2014-11-20")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "date_obj1" not in data
    assert "date_obj2" in data

    # date - empty
    rv = client.get("/admin/_datetime/?flt0_6=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" in data
    assert "date_obj1" not in data
    assert "date_obj2" not in data

    # date - empty
    rv = client.get("/admin/_datetime/?flt0_6=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" not in data
    assert "date_obj1" in data
    assert "date_obj2" in data

    # datetime - equals
    rv = client.get("/admin/_datetime/?flt0_7=2014-04-03+01%3A09%3A00")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" in data
    assert "datetime_obj2" not in data

    # datetime - not equal
    rv = client.get("/admin/_datetime/?flt0_8=2014-04-03+01%3A09%3A00")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" not in data
    assert "datetime_obj2" in data

    # datetime - greater
    rv = client.get("/admin/_datetime/?flt0_9=2014-04-03+01%3A08%3A00")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" in data
    assert "datetime_obj2" not in data

    # datetime - smaller
    rv = client.get("/admin/_datetime/?flt0_10=2014-04-03+01%3A08%3A00")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" not in data
    assert "datetime_obj2" in data

    # datetime - between
    rv = client.get(
        "/admin/_datetime/?flt0_11=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
    )
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" in data
    assert "datetime_obj2" not in data

    # datetime - not between
    rv = client.get(
        "/admin/_datetime/?flt0_12=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
    )
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "datetime_obj1" not in data
    assert "datetime_obj2" in data

    # datetime - empty
    rv = client.get("/admin/_datetime/?flt0_13=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" in data
    assert "datetime_obj1" not in data
    assert "datetime_obj2" not in data

    # datetime - not empty
    rv = client.get("/admin/_datetime/?flt0_13=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" not in data
    assert "datetime_obj1" in data
    assert "datetime_obj2" in data

    # time - equals
    rv = client.get("/admin/_datetime/?flt0_14=11%3A10%3A09")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" in data
    assert "timeonly_obj2" not in data

    # time - not equal
    rv = client.get("/admin/_datetime/?flt0_15=11%3A10%3A09")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" not in data
    assert "timeonly_obj2" in data

    # time - greater
    rv = client.get("/admin/_datetime/?flt0_16=11%3A09%3A09")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" in data
    assert "timeonly_obj2" not in data

    # time - smaller
    rv = client.get("/admin/_datetime/?flt0_17=11%3A09%3A09")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" not in data
    assert "timeonly_obj2" in data

    # time - between
    rv = client.get("/admin/_datetime/?flt0_18=10%3A40%3A00+to+11%3A50%3A59")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" in data
    assert "timeonly_obj2" not in data

    # time - not between
    rv = client.get("/admin/_datetime/?flt0_19=10%3A40%3A00+to+11%3A50%3A59")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "timeonly_obj1" not in data
    assert "timeonly_obj2" in data

    # time - empty
    rv = client.get("/admin/_datetime/?flt0_20=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" in data
    assert "timeonly_obj1" not in data
    assert "timeonly_obj2" not in data

    # time - not empty
    rv = client.get("/admin/_datetime/?flt0_20=0")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1_val_1" not in data
    assert "timeonly_obj1" in data
    assert "timeonly_obj2" in data


def test_default_sort(app, db, admin):
    M1, _ = create_models(db)

    M1("c", 1).save()
    M1("b", 1).save()
    M1("a", 2).save()

    assert M1.select().count() == 3

    view = CustomModelView(M1, column_default_sort="test1")
    admin.add_view(view)

    _, data = view.get_list(0, None, None, None, None)

    assert data[0].test1 == "a"
    assert data[1].test1 == "b"
    assert data[2].test1 == "c"

    # test default sort with multiple columns
    order = [("test2", False), ("test1", False)]
    view2 = CustomModelView(M1, column_default_sort=order, endpoint="m1_2")
    admin.add_view(view2)

    _, data = view2.get_list(0, None, None, None, None)

    assert len(data) == 3
    assert data[0].test1 == "b"
    assert data[1].test1 == "c"
    assert data[2].test1 == "a"


def test_extra_fields(app, db, admin):
    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1, form_extra_fields={"extra_field": fields.StringField("Extra Field")}
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


def test_custom_form_base(app, db, admin):
    class TestForm(form.BaseForm):
        pass

    Model1, _ = create_models(db)

    view = CustomModelView(Model1, form_base_class=TestForm)
    admin.add_view(view)

    assert hasattr(view._create_form_class, "test1")

    create_form = view.create_form()
    assert isinstance(create_form, TestForm)


def test_form_args(app, db, admin):
    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model(BaseModel):
        test = peewee.CharField(null=False)

    Model.create_table()

    shared_form_args = {"test": {"validators": [validators.Regexp("test")]}}

    view = CustomModelView(Model, form_args=shared_form_args)
    admin.add_view(view)

    # ensure shared field_args don't create duplicate validators
    create_form = view.create_form()

    assert len(create_form.test.validators) == 2

    edit_form = view.edit_form()
    assert len(edit_form.test.validators) == 2


def test_ajax_fk(app, db, admin):
    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model1(BaseModel):
        test1 = peewee.CharField(max_length=20)
        test2 = peewee.CharField(max_length=20)

        def __str__(self):
            return self.test1

    class Model2(BaseModel):
        model1 = peewee.ForeignKeyField(Model1)

    Model1.create_table()
    Model2.create_table()

    view = CustomModelView(
        Model2, url="view", form_ajax_refs={"model1": {"fields": ("test1", "test2")}}
    )
    admin.add_view(view)

    assert "model1" in view._form_ajax_refs

    model = Model1(test1="first", test2="")
    model.save()
    model2 = Model1(test1="foo", test2="bar")
    model2.save()

    # Check loader
    loader = view._form_ajax_refs["model1"]
    mdl = loader.get_one(model.id)
    assert mdl.test1 == model.test1

    items = loader.get_list("fir")
    assert len(items) == 1
    assert items[0].id == model.id

    items = loader.get_list("bar")
    assert len(items) == 1
    assert items[0].test1 == "foo"

    # Check form generation
    form = view.create_form()
    assert form.model1.__class__.__name__ == "AjaxSelectField"

    with app.test_request_context("/admin/view/"):
        assert 'value=""' not in form.model1()

        form.model1.data = model
        assert (
            f'data-json="[{as_unicode(model.id)}, &quot;first&quot;]"' in form.model1()
            or f'data-json="[{as_unicode(model.id)}, &#34;first&#34;]"'
        )
        assert f'value="{as_unicode(model.id)}"' in form.model1()

    # Check querying
    client = app.test_client()

    req = client.get("/admin/view/ajax/lookup/?name=model1&query=foo")
    assert req.data == b'[[%d, "foo"]]' % model2.id

    # Check submitting
    client.post("/admin/view/new/", data={"model1": as_unicode(model.id)})
    mdl = Model2.select().first()

    assert mdl is not None
    assert mdl.model1 is not None
    assert mdl.model1.id == model.id
    assert mdl.model1.test1 == "first"


def test_customising_page_size(app, db, admin):
    with app.app_context():
        M1, _ = create_models(db)

        instances = [M1(f"instance-{x+1:03d}") for x in range(101)]
        for instance in instances:
            instance.save()

        view1 = CustomModelView(
            M1, endpoint="view1", page_size=20, can_set_page_size=False
        )
        admin.add_view(view1)

        view2 = CustomModelView(
            M1, db, endpoint="view2", page_size=5, can_set_page_size=False
        )
        admin.add_view(view2)

        view3 = CustomModelView(
            M1, db, endpoint="view3", page_size=20, can_set_page_size=True
        )
        admin.add_view(view3)

        view4 = CustomModelView(
            M1,
            db,
            endpoint="view4",
            page_size=5,
            page_size_options=(5, 10, 15),
            can_set_page_size=True,
        )
        admin.add_view(view4)

        client = app.test_client()

        rv = client.get("/admin/view1/")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # `can_set_page_size=False`, so only the default of 20 is available.
        rv = client.get("/admin/view1/?page_size=50")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # Check view2, which has `page_size=5` to change the default page size
        rv = client.get("/admin/view2/")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        # Check view3, which has `can_set_page_size=True`
        rv = client.get("/admin/view3/")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        rv = client.get("/admin/view3/?page_size=50")
        assert "instance-050" in rv.text
        assert "instance-051" not in rv.text

        rv = client.get("/admin/view3/?page_size=100")
        assert "instance-100" in rv.text
        assert "instance-101" not in rv.text

        # Invalid page sizes are reset to the default
        rv = client.get("/admin/view3/?page_size=1")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # Check view4, which has custom `page_size_options`
        rv = client.get("/admin/view4/")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        # Invalid page sizes are reset to the default
        rv = client.get("/admin/view4/?page_size=1")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        rv = client.get("/admin/view4/?page_size=10")
        assert "instance-010" in rv.text
        assert "instance-011" not in rv.text

        rv = client.get("/admin/view4/?page_size=15")
        assert "instance-015" in rv.text
        assert "instance-016" not in rv.text


def test_export_csv(app, db, admin):
    Model1, Model2 = create_models(db)

    view = CustomModelView(
        Model1,
        can_export=True,
        column_list=["test1", "test2"],
        export_max_rows=2,
        endpoint="row_limit_2",
    )
    admin.add_view(view)

    view2 = CustomModelView(
        Model1, can_export=True, column_list=["test1", "test2"], endpoint="no_row_limit"
    )
    admin.add_view(view2)

    for _x in range(5):
        fill_db(Model1, Model2)

    client = app.test_client()

    # test export_max_rows
    rv = client.get("/admin/row_limit_2/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert (
        "Test1,Test2\r\n"
        + "test1_val_1,test2_val_1\r\n"
        + "test1_val_2,test2_val_2\r\n"
        == data
    )

    # test row limit without export_max_rows
    rv = client.get("/admin/no_row_limit/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert len(data.splitlines()) > 21
