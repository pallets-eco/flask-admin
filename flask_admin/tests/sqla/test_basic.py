import enum
import uuid
from datetime import date
from datetime import datetime
from datetime import time

import arrow
import pytest
from sqlalchemy import cast
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType
from wtforms import fields
from wtforms import validators

from flask_admin import form
from flask_admin._compat import as_unicode
from flask_admin._compat import iteritems
from flask_admin.contrib.sqla import filters
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla import tools
from flask_admin.form.fields import DateTimeField
from flask_admin.form.fields import Select2Field
from flask_admin.tests import flask_babel_test_decorator


class CustomModelView(ModelView):
    def __init__(
        self,
        model,
        session,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        **kwargs,
    ):
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super().__init__(model, session, name, category, endpoint, url)

    form_choices = {"choice_field": [("choice-1", "One"), ("choice-2", "Two")]}


def create_models(db):
    class Model1(db.Model):
        def __init__(
            self,
            test1=None,
            test2=None,
            test3=None,
            test4=None,
            bool_field=False,
            date_field=None,
            time_field=None,
            datetime_field=None,
            email_field=None,
            choice_field=None,
            enum_field=None,
            enum_type_field=None,
        ):
            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4
            self.bool_field = bool_field
            self.date_field = date_field
            self.time_field = time_field
            self.datetime_field = datetime_field
            self.email_field = email_field
            self.choice_field = choice_field
            self.enum_field = enum_field
            self.enum_type_field = enum_type_field

        class EnumChoices(enum.Enum):
            first = 1
            second = 2

        id = db.Column(db.Integer, primary_key=True)
        test1 = db.Column(db.String(20))
        test2 = db.Column(db.Unicode(20))
        test3 = db.Column(db.Text)
        test4 = db.Column(db.UnicodeText)
        bool_field = db.Column(db.Boolean)
        date_field = db.Column(db.Date)
        time_field = db.Column(db.Time)
        datetime_field = db.Column(db.DateTime)
        email_field = db.Column(EmailType)
        enum_field = db.Column(db.Enum("model1_v1", "model1_v2"), nullable=True)
        enum_type_field = db.Column(db.Enum(EnumChoices), nullable=True)
        choice_field = db.Column(db.String, nullable=True)
        sqla_utils_choice = db.Column(
            ChoiceType([("choice-1", "First choice"), ("choice-2", "Second choice")])
        )
        sqla_utils_enum = db.Column(ChoiceType(EnumChoices, impl=db.Integer()))
        sqla_utils_arrow = db.Column(ArrowType, default=arrow.utcnow())
        sqla_utils_uuid = db.Column(UUIDType(binary=False), default=uuid.uuid4)
        sqla_utils_url = db.Column(URLType)
        sqla_utils_ip_address = db.Column(IPAddressType)
        sqla_utils_currency = db.Column(CurrencyType)
        sqla_utils_color = db.Column(ColorType)

        def __unicode__(self):
            return self.test1

        def __str__(self):
            return self.test1

    class Model2(db.Model):
        def __init__(
            self,
            string_field=None,
            int_field=None,
            bool_field=None,
            model1=None,
            float_field=None,
            string_field_default=None,
            string_field_empty_default=None,
        ):
            self.string_field = string_field
            self.int_field = int_field
            self.bool_field = bool_field
            self.model1 = model1
            self.float_field = float_field
            self.string_field_default = string_field_default
            self.string_field_empty_default = string_field_empty_default

        id = db.Column(db.Integer, primary_key=True)
        string_field = db.Column(db.String)
        string_field_default = db.Column(db.Text, nullable=False, default="")
        string_field_empty_default = db.Column(db.Text, nullable=False, default="")
        int_field = db.Column(db.Integer)
        bool_field = db.Column(db.Boolean)
        enum_field = db.Column(db.Enum("model2_v1", "model2_v2"), nullable=True)
        float_field = db.Column(db.Float)

        # Relation
        model1_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
        model1 = db.relationship(lambda: Model1, backref="model2")

    db.create_all()

    return Model1, Model2


def fill_db(db, Model1, Model2):
    model1_obj1 = Model1("test1_val_1", "test2_val_1", bool_field=True)
    model1_obj2 = Model1("test1_val_2", "test2_val_2", bool_field=False)
    model1_obj3 = Model1("test1_val_3", "test2_val_3")
    model1_obj4 = Model1(
        "test1_val_4",
        "test2_val_4",
        email_field="test@test.com",
        choice_field="choice-1",
    )

    model2_obj1 = Model2("test2_val_1", model1=model1_obj1, float_field=None)
    model2_obj2 = Model2("test2_val_2", model1=model1_obj2, float_field=None)
    model2_obj3 = Model2("test2_val_3", int_field=5000, float_field=25.9)
    model2_obj4 = Model2("test2_val_4", int_field=9000, float_field=75.5)
    model2_obj5 = Model2("test2_val_5", int_field=6169453081680413441)

    date_obj1 = Model1("date_obj1", date_field=date(2014, 11, 17))
    date_obj2 = Model1("date_obj2", date_field=date(2013, 10, 16))
    timeonly_obj1 = Model1("timeonly_obj1", time_field=time(11, 10, 9))
    timeonly_obj2 = Model1("timeonly_obj2", time_field=time(10, 9, 8))
    datetime_obj1 = Model1(
        "datetime_obj1", datetime_field=datetime(2014, 4, 3, 1, 9, 0)
    )
    datetime_obj2 = Model1(
        "datetime_obj2", datetime_field=datetime(2013, 3, 2, 0, 8, 0)
    )

    enum_obj1 = Model1("enum_obj1", enum_field="model1_v1")
    enum_obj2 = Model1("enum_obj2", enum_field="model1_v2")

    enum_type_obj1 = Model1("enum_type_obj1", enum_type_field=Model1.EnumChoices.first)
    enum_type_obj2 = Model1("enum_type_obj2", enum_type_field=Model1.EnumChoices.second)

    empty_obj = Model1(test2="empty_obj")

    db.session.add_all(
        [
            model1_obj1,
            model1_obj2,
            model1_obj3,
            model1_obj4,
            model2_obj1,
            model2_obj2,
            model2_obj3,
            model2_obj4,
            model2_obj5,
            date_obj1,
            timeonly_obj1,
            datetime_obj1,
            date_obj2,
            timeonly_obj2,
            datetime_obj2,
            enum_obj1,
            enum_obj2,
            enum_type_obj1,
            enum_type_obj2,
            empty_obj,
        ]
    )
    db.session.commit()


@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
def test_model(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(Model1, db.session)

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
        assert view._create_form_class.email_field.field_class == fields.StringField
        assert view._create_form_class.choice_field.field_class == Select2Field
        assert view._create_form_class.enum_field.field_class == Select2Field
        assert view._create_form_class.sqla_utils_choice.field_class == Select2Field
        assert view._create_form_class.sqla_utils_enum.field_class == Select2Field
        assert view._create_form_class.sqla_utils_arrow.field_class == DateTimeField
        assert view._create_form_class.sqla_utils_uuid.field_class == fields.StringField
        assert view._create_form_class.sqla_utils_url.field_class == fields.StringField
        assert (
            view._create_form_class.sqla_utils_ip_address.field_class
            == fields.StringField
        )
        assert (
            view._create_form_class.sqla_utils_currency.field_class
            == fields.StringField
        )
        assert (
            view._create_form_class.sqla_utils_color.field_class == fields.StringField
        )

        # Make some test clients
        client = app.test_client()

        # check that we can retrieve a list view
        rv = client.get("/admin/model1/")
        assert rv.status_code == 200

        # check that we can retrieve a 'create' view
        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        # create a new record
        uuid_obj = uuid.uuid4()
        rv = client.post(
            "/admin/model1/new/",
            data=dict(
                test1="test1large",
                test2="test2",
                time_field=time(0, 0, 0),
                email_field="Test@TEST.com",
                choice_field="choice-1",
                enum_field="model1_v1",
                sqla_utils_choice="choice-1",
                sqla_utils_enum=1,
                sqla_utils_arrow="2018-10-27 14:17:00",
                sqla_utils_uuid=str(uuid_obj),
                sqla_utils_url="http://www.example.com",
                sqla_utils_ip_address="127.0.0.1",
                sqla_utils_currency="USD",
                sqla_utils_color="#f0f0f0",
            ),
        )
        assert rv.status_code == 302

        # check that the new record was persisted
        model = db.session.query(Model1).first()
        assert model.test1 == "test1large"
        assert model.test2 == "test2"
        assert model.test3 is None
        assert model.test4 is None
        assert model.email_field == "test@test.com"
        assert model.choice_field == "choice-1"
        assert model.enum_field == "model1_v1"
        assert model.sqla_utils_choice == "choice-1"
        assert model.sqla_utils_enum.value == 1
        assert model.sqla_utils_arrow == arrow.get("2018-10-27 14:17:00")
        assert model.sqla_utils_uuid == uuid_obj
        assert model.sqla_utils_url == "http://www.example.com"
        assert str(model.sqla_utils_ip_address) == "127.0.0.1"
        assert str(model.sqla_utils_currency) == "USD"
        assert model.sqla_utils_color.hex == "#f0f0f0"

        # check that the new record shows up on the list view
        rv = client.get("/admin/model1/")
        assert rv.status_code == 200
        assert "test1large" in rv.data.decode("utf-8")

        # check that we can retrieve an edit view
        url = f"/admin/model1/edit/?id={model.id}"
        rv = client.get(url)
        assert rv.status_code == 200

        # verify that midnight does not show as blank
        assert "00:00:00" in rv.data.decode("utf-8")

        # edit the record
        new_uuid_obj = uuid.uuid4()
        rv = client.post(
            url,
            data=dict(
                test1="test1small",
                test2="test2large",
                email_field="Test2@TEST.com",
                choice_field="__None",
                enum_field="__None",
                sqla_utils_choice="__None",
                sqla_utils_enum="__None",
                sqla_utils_arrow="",
                sqla_utils_uuid=str(new_uuid_obj),
                sqla_utils_url="",
                sqla_utils_ip_address="",
                sqla_utils_currency="",
                sqla_utils_color="",
            ),
        )
        assert rv.status_code == 302

        # check that the changes were persisted
        model = db.session.query(Model1).first()
        assert model.test1 == "test1small"
        assert model.test2 == "test2large"
        assert model.test3 is None
        assert model.test4 is None
        assert model.email_field == "test2@test.com"
        assert model.choice_field is None
        assert model.enum_field is None
        assert model.sqla_utils_choice is None
        assert model.sqla_utils_enum is None
        assert model.sqla_utils_arrow is None
        assert model.sqla_utils_uuid == new_uuid_obj
        assert model.sqla_utils_url is None
        assert model.sqla_utils_ip_address is None
        assert model.sqla_utils_currency is None
        assert model.sqla_utils_color is None

        # check that the model can be deleted
        url = f"/admin/model1/delete/?id={model.id}"
        rv = client.post(url)
        assert rv.status_code == 302
        assert db.session.query(Model1).count() == 0


@pytest.mark.xfail(raises=Exception)
def test_no_pk(app, db, admin):
    class Model(db.Model):
        test = db.Column(db.Integer)

    view = CustomModelView(Model)
    admin.add_view(view)


def test_list_columns(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        # test column_list with a list of strings
        view = CustomModelView(
            Model1,
            db.session,
            column_list=["test1", "test3"],
            column_labels=dict(test1="Column1"),
        )
        admin.add_view(view)

        # test column_list with a list of SQLAlchemy columns
        view2 = CustomModelView(
            Model1,
            db.session,
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


def test_complex_list_columns(app, db, admin):
    with app.app_context():
        M1, M2 = create_models(db)

        m1 = M1("model1_val1")
        db.session.add(m1)
        db.session.add(M2("model2_val1", model1=m1))

        db.session.commit()

        # test column_list with a list of strings on a relation
        view = CustomModelView(M2, db.session, column_list=["model1.test1"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "model1_val1" in data


def test_exclude_columns(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
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
            ],
        )
        admin.add_view(view)

        assert view._list_columns == [
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
        assert "Test2" not in data


def test_column_searchable_list(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model2, db.session, column_searchable_list=["string_field", "int_field"]
        )
        admin.add_view(view)

        assert view._search_supported
        assert len(view._search_fields) == 2

        assert isinstance(view._search_fields[0][0], db.Column)
        assert isinstance(view._search_fields[1][0], db.Column)
        assert view._search_fields[0][0].name == "string_field"
        assert view._search_fields[1][0].name == "int_field"

        db.session.add(Model2("model1-test", 5000))
        db.session.add(Model2("model2-test", 9000))
        db.session.commit()

        client = app.test_client()

        rv = client.get("/admin/model2/?search=model1")
        data = rv.data.decode("utf-8")
        assert "model1-test" in data
        assert "model2-test" not in data

        rv = client.get("/admin/model2/?search=9000")
        data = rv.data.decode("utf-8")
        assert "model1-test" not in data
        assert "model2-test" in data


def test_extra_args_search(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view1 = CustomModelView(
            Model1,
            db.session,
            column_searchable_list=[
                "test1",
            ],
        )

        admin.add_view(view1)

        db.session.add(
            Model2(
                "model1-test",
            )
        )
        db.session.commit()

        client = app.test_client()

        # check that extra args in the url are propagated as hidden fields in the
        # search form
        rv = client.get("/admin/model1/?search=model1&foo=bar")
        data = rv.data.decode("utf-8")
        assert '<input type="hidden" name="foo" value="bar">' in data


def test_extra_args_filter(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view2 = CustomModelView(
            Model2,
            db.session,
            column_filters=[
                "int_field",
            ],
        )
        admin.add_view(view2)

        db.session.add(Model2("model2-test", 5000))
        db.session.commit()

        client = app.test_client()

        # check that extra args in the url are propagated as hidden fields in the  form
        rv = client.get("/admin/model2/?flt1_0=5000&foo=bar")
        data = rv.data.decode("utf-8")
        assert '<input type="hidden" name="foo" value="bar">' in data


def test_complex_searchable_list(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model2, db.session, column_searchable_list=["model1.test1"]
        )
        admin.add_view(view)
        view2 = CustomModelView(
            Model1, db.session, column_searchable_list=[Model2.string_field]
        )
        admin.add_view(view2)

        m1 = Model1("model1-test1-val")
        m2 = Model1("model1-test2-val")
        db.session.add(m1)
        db.session.add(m2)
        db.session.add(Model2("model2-test1-val", model1=m1))
        db.session.add(Model2("model2-test2-val", model1=m2))
        db.session.commit()

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


def test_complex_searchable_list_missing_children(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model1, db.session, column_searchable_list=["test1", "model2.string_field"]
        )
        admin.add_view(view)

        db.session.add(Model1("magic string"))
        db.session.commit()

        client = app.test_client()

        rv = client.get("/admin/model1/?search=magic")
        data = rv.data.decode("utf-8")
        assert "magic string" in data


def test_column_editable_list(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model1, db.session, column_editable_list=["test1", "enum_field"]
        )
        admin.add_view(view)

        # Test in-line editing for relations
        view = CustomModelView(Model2, db.session, column_editable_list=["model1"])
        admin.add_view(view)

        fill_db(db, Model1, Model2)

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


def test_details_view(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view_no_details = CustomModelView(Model1, db.session)
        admin.add_view(view_no_details)

        # fields are scaffolded
        view_w_details = CustomModelView(Model2, db.session, can_view_details=True)
        admin.add_view(view_w_details)

        # show only specific fields in details w/ column_details_list
        string_field_view = CustomModelView(
            Model2,
            db.session,
            can_view_details=True,
            column_details_list=["string_field"],
            endpoint="sf_view",
        )
        admin.add_view(string_field_view)

        fill_db(db, Model1, Model2)

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


def test_editable_list_special_pks(app, db, admin):
    """Tests editable list view + a primary key with special characters"""
    with app.app_context():

        class Model1(db.Model):
            def __init__(self, id=None, val1=None):
                self.id = id
                self.val1 = val1

            id = db.Column(db.String(20), primary_key=True)
            val1 = db.Column(db.String(20))

        db.create_all()

        view = CustomModelView(Model1, db.session, column_editable_list=["val1"])
        admin.add_view(view)

        db.session.add(Model1("1-1", "test1"))
        db.session.add(Model1("1-5", "test2"))
        db.session.commit()

        client = app.test_client()

        # Form - Test basic in-line edit functionality
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1-1",
                "val1": "change-success-1",
            },
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully saved." == data

        # ensure the value has changed
        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "change-success-1" in data


def test_column_filters(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view1 = CustomModelView(Model1, db.session, column_filters=["test1"])
        admin.add_view(view1)

        client = app.test_client()

        assert len(view1._filters) == 7

        # Generate views
        view2 = CustomModelView(Model2, db.session, column_filters=["model1"])

        view5 = CustomModelView(
            Model1, db.session, column_filters=["test1"], endpoint="_strings"
        )
        admin.add_view(view5)

        view6 = CustomModelView(Model2, db.session, column_filters=["int_field"])
        admin.add_view(view6)

        view7 = CustomModelView(
            Model1, db.session, column_filters=["bool_field"], endpoint="_bools"
        )
        admin.add_view(view7)

        view8 = CustomModelView(
            Model2, db.session, column_filters=["float_field"], endpoint="_float"
        )
        admin.add_view(view8)

        view9 = CustomModelView(
            Model2,
            db.session,
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
            db.session,
            column_filters=["test1"],
            endpoint="_model3",
            named_filter_urls=True,
        )
        admin.add_view(view10)

        view11 = CustomModelView(
            Model1,
            db.session,
            column_filters=["date_field", "datetime_field", "time_field"],
            endpoint="_datetime",
        )
        admin.add_view(view11)

        view12 = CustomModelView(
            Model1, db.session, column_filters=["enum_field"], endpoint="_enumfield"
        )
        admin.add_view(view12)

        view13 = CustomModelView(
            Model2,
            db.session,
            column_filters=[filters.FilterEqual(Model1.test1, "Test1")],
            endpoint="_relation_test",
        )
        admin.add_view(view13)

        view14 = CustomModelView(
            Model1,
            db.session,
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
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test1"]
        ] == [
            (0, "contains"),
            (1, "not contains"),
            (2, "equals"),
            (3, "not equal"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test2"]
        ] == [
            (7, "contains"),
            (8, "not contains"),
            (9, "equals"),
            (10, "not equal"),
            (11, "empty"),
            (12, "in list"),
            (13, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test3"]
        ] == [
            (14, "contains"),
            (15, "not contains"),
            (16, "equals"),
            (17, "not equal"),
            (18, "empty"),
            (19, "in list"),
            (20, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test4"]
        ] == [
            (21, "contains"),
            (22, "not contains"),
            (23, "equals"),
            (24, "not equal"),
            (25, "empty"),
            (26, "in list"),
            (27, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Bool Field"]
        ] == [
            (28, "equals"),
            (29, "not equal"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Date Field"]
        ] == [
            (30, "equals"),
            (31, "not equal"),
            (32, "greater than"),
            (33, "smaller than"),
            (34, "between"),
            (35, "not between"),
            (36, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Time Field"]
        ] == [
            (37, "equals"),
            (38, "not equal"),
            (39, "greater than"),
            (40, "smaller than"),
            (41, "between"),
            (42, "not between"),
            (43, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Datetime Field"]
        ] == [
            (44, "equals"),
            (45, "not equal"),
            (46, "greater than"),
            (47, "smaller than"),
            (48, "between"),
            (49, "not between"),
            (50, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Email Field"]
        ] == [
            (51, "contains"),
            (52, "not contains"),
            (53, "equals"),
            (54, "not equal"),
            (55, "empty"),
            (56, "in list"),
            (57, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Enum Field"]
        ] == [
            (58, "equals"),
            (59, "not equal"),
            (60, "empty"),
            (61, "in list"),
            (62, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Enum Type Field"]
        ] == [
            (63, "equals"),
            (64, "not equal"),
            (65, "empty"),
            (66, "in list"),
            (67, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Choice Field"]
        ] == [
            (68, "contains"),
            (69, "not contains"),
            (70, "equals"),
            (71, "not equal"),
            (72, "empty"),
            (73, "in list"),
            (74, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Sqla Utils Choice"]
        ] == [
            (75, "equals"),
            (76, "not equal"),
            (77, "contains"),
            (78, "not contains"),
            (79, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Sqla Utils Enum"]
        ] == [
            (80, "equals"),
            (81, "not equal"),
            (82, "contains"),
            (83, "not contains"),
            (84, "empty"),
        ]

        # Test filter with a dot
        view3 = CustomModelView(
            Model2, db.session, column_filters=["model1.bool_field"]
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
            db.session,
            column_filters=["model1.bool_field", "string_field"],
            column_labels={
                "model1.bool_field": "Test Filter #1",
                "string_field": "Test Filter #2",
            },
        )

        assert list(view4._filter_groups.keys()) == ["Test Filter #1", "Test Filter #2"]

        fill_db(db, Model1, Model2)

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

        # string - not equal
        rv = client.get("/admin/_strings/?flt0_1=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test1_val_2" in data

        # string - contains
        rv = client.get("/admin/_strings/?flt0_2=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test1_val_2" not in data

        # string - not contains
        rv = client.get("/admin/_strings/?flt0_3=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test1_val_2" in data

        # string - empty
        rv = client.get("/admin/_strings/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "empty_obj" in data
        assert "test1_val_1" not in data
        assert "test1_val_2" not in data

        # string - not empty
        rv = client.get("/admin/_strings/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "empty_obj" not in data
        assert "test1_val_1" in data
        assert "test1_val_2" in data

        # string - in list
        rv = client.get("/admin/_strings/?flt0_5=test1_val_1%2Ctest1_val_2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test1_val_3" not in data
        assert "test1_val_4" not in data

        # string - not in list
        rv = client.get("/admin/_strings/?flt0_6=test1_val_1%2Ctest1_val_2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test1_val_3" in data
        assert "test1_val_4" in data

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

        # integer - equals (huge number)
        rv = client.get("/admin/model2/?flt0_0=6169453081680413441")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_5" in data
        assert "test2_val_4" not in data

        # integer - equals - test validation
        rv = client.get("/admin/model2/?flt0_0=badval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # integer - not equal
        rv = client.get("/admin/model2/?flt0_1=5000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # integer - greater
        rv = client.get("/admin/model2/?flt0_2=6000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # integer - smaller
        rv = client.get("/admin/model2/?flt0_3=6000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # integer - empty
        rv = client.get("/admin/model2/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # integer - not empty
        rv = client.get("/admin/model2/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # integer - in list
        rv = client.get("/admin/model2/?flt0_5=5000%2C9000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # integer - in list (huge number)
        rv = client.get("/admin/model2/?flt0_5=6169453081680413441")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_5" in data

        # integer - in list - test validation
        rv = client.get("/admin/model2/?flt0_5=5000%2Cbadval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # integer - not in list
        rv = client.get("/admin/model2/?flt0_6=5000%2C9000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
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
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data

        # boolean - equals - No
        rv = client.get("/admin/_bools/?flt0_0=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" in data
        assert "test2_val_3" in data

        # boolean - not equals - Yes
        rv = client.get("/admin/_bools/?flt0_1=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" in data
        assert "test2_val_3" in data

        # boolean - not equals - No
        rv = client.get("/admin/_bools/?flt0_1=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data

        # Test float filter
        assert [
            (f["index"], f["operation"]) for f in view8._filter_groups["Float Field"]
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
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # float - equals - test validation
        rv = client.get("/admin/_float/?flt0_0=badval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # float - not equal
        rv = client.get("/admin/_float/?flt0_1=25.9")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # float - greater
        rv = client.get("/admin/_float/?flt0_2=60.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # float - smaller
        rv = client.get("/admin/_float/?flt0_3=60.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # float - empty
        rv = client.get("/admin/_float/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # float - not empty
        rv = client.get("/admin/_float/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # float - in list
        rv = client.get("/admin/_float/?flt0_5=25.9%2C75.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # float - in list - test validation
        rv = client.get("/admin/_float/?flt0_5=25.9%2Cbadval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # float - not in list
        rv = client.get("/admin/_float/?flt0_6=25.9%2C75.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # Test filters to joined table field
        rv = client.get("/admin/_model2/?flt1_0=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # Test human readable URLs
        rv = client.get("/admin/_model3/?flt1_test1_equals=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "test1_val_2" not in data

        # Test date, time, and datetime filters
        assert [
            (f["index"], f["operation"]) for f in view11._filter_groups["Date Field"]
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
            (f["index"], f["operation"])
            for f in view11._filter_groups["Datetime Field"]
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
            (f["index"], f["operation"]) for f in view11._filter_groups["Time Field"]
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
            "/admin/_datetime"
            "/?flt0_11=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
        )
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" in data
        assert "datetime_obj2" not in data

        # datetime - not between
        rv = client.get(
            "/admin/_datetime"
            "/?flt0_12=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
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

        # Test enum filter
        # enum - equals
        rv = client.get("/admin/_enumfield/?flt0_0=model1_v1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_obj1" in data
        assert "enum_obj2" not in data

        # enum - not equal
        rv = client.get("/admin/_enumfield/?flt0_1=model1_v1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_obj1" not in data
        assert "enum_obj2" in data

        # enum - empty
        rv = client.get("/admin/_enumfield/?flt0_2=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_obj1" not in data
        assert "enum_obj2" not in data

        # enum - not empty
        rv = client.get("/admin/_enumfield/?flt0_2=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_obj1" in data
        assert "enum_obj2" in data

        # enum - in list
        rv = client.get("/admin/_enumfield/?flt0_3=model1_v1%2Cmodel1_v2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_obj1" in data
        assert "enum_obj2" in data

        # enum - not in list
        rv = client.get("/admin/_enumfield/?flt0_4=model1_v1%2Cmodel1_v2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_obj1" not in data
        assert "enum_obj2" not in data

        # Test enum type filter
        # enum type - equals
        rv = client.get("/admin/_enumtypefield/?flt0_0=first")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" not in data

        # enum - not equal
        rv = client.get("/admin/_enumtypefield/?flt0_1=first")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" in data

        # enum - empty
        rv = client.get("/admin/_enumtypefield/?flt0_2=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" not in data

        # enum - not empty
        rv = client.get("/admin/_enumtypefield/?flt0_2=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" in data

        # enum - in list
        rv = client.get("/admin/_enumtypefield/?flt0_3=first%2Csecond")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" in data

        # enum - not in list
        rv = client.get("/admin/_enumtypefield/?flt0_4=first%2Csecond")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" not in data

        # Test single custom filter on relation
        rv = client.get("/admin/_relation_test/?flt1_0=test1_val_1")
        data = rv.data.decode("utf-8")

        assert "test1_val_1" in data
        assert "test1_val_2" not in data


def test_column_filters_sqla_obj(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(Model1, db.session, column_filters=[Model1.test1])
        admin.add_view(view)

        assert len(view._filters) == 7


def test_hybrid_property(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            width = db.Column(db.Integer)
            height = db.Column(db.Integer)

            @hybrid_property
            def number_of_pixels(self):
                return self.width * self.height

            @hybrid_property
            def number_of_pixels_str(self):
                return str(self.number_of_pixels())

            @number_of_pixels_str.expression
            def number_of_pixels_str(cls):
                return cast(cls.width * cls.height, db.String)

        db.create_all()

        assert tools.is_hybrid_property(Model1, "number_of_pixels")
        assert tools.is_hybrid_property(Model1, "number_of_pixels_str")
        assert not tools.is_hybrid_property(Model1, "height")
        assert not tools.is_hybrid_property(Model1, "width")

        db.session.add(Model1(id=1, name="test_row_1", width=25, height=25))
        db.session.add(Model1(id=2, name="test_row_2", width=10, height=10))
        db.session.commit()

        client = app.test_client()

        view = CustomModelView(
            Model1,
            db.session,
            column_default_sort="number_of_pixels",
            column_filters=[
                filters.IntGreaterFilter(Model1.number_of_pixels, "Number of Pixels")
            ],
            column_searchable_list=[
                "number_of_pixels_str",
            ],
        )
        admin.add_view(view)

        # filters - hybrid_property integer - greater
        rv = client.get("/admin/model1/?flt0_0=600")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_row_1" in data
        assert "test_row_2" not in data

        # sorting
        rv = client.get("/admin/model1/?sort=0")
        assert rv.status_code == 200

        _, data = view.get_list(0, None, None, None, None)

        assert len(data) == 2
        assert data[0].name == "test_row_2"
        assert data[1].name == "test_row_1"

        # searching
        rv = client.get("/admin/model1/?search=100")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_row_2" in data
        assert "test_row_1" not in data


def test_hybrid_property_nested(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            firstname = db.Column(db.String)
            lastname = db.Column(db.String)

            @hybrid_property
            def fullname(self):
                return f"{self.firstname} {self.lastname}"

        class Model2(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            owner_id = db.Column(
                db.Integer, db.ForeignKey("model1.id", ondelete="CASCADE")
            )
            owner = db.relationship(
                "Model1", backref=db.backref("tiles"), uselist=False
            )

        db.create_all()

        assert tools.is_hybrid_property(Model2, "owner.fullname")
        assert not tools.is_hybrid_property(Model2, "owner.firstname")

        db.session.add(Model1(id=1, firstname="John", lastname="Dow"))
        db.session.add(Model1(id=2, firstname="Jim", lastname="Smith"))
        db.session.add(Model2(id=1, name="pencil", owner_id=1))
        db.session.add(Model2(id=2, name="key", owner_id=1))
        db.session.add(Model2(id=3, name="map", owner_id=2))
        db.session.commit()

        client = app.test_client()

        view = CustomModelView(
            Model2,
            db.session,
            column_list=("id", "name", "owner.fullname"),
            column_default_sort="id",
        )
        admin.add_view(view)

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "John Dow" in data
        assert "Jim Smith" in data


def test_url_args(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
            page_size=2,
            column_searchable_list=["test1"],
            column_filters=["test1"],
        )
        admin.add_view(view)

        db.session.add(Model1("data1"))
        db.session.add(Model1("data2"))
        db.session.add(Model1("data3"))
        db.session.add(Model1("data4"))
        db.session.commit()

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


def test_non_int_pk(app, db, admin):
    with app.app_context():

        class Model(db.Model):
            id = db.Column(db.String, primary_key=True)
            test = db.Column(db.String)

        db.create_all()

        view = CustomModelView(Model, db.session, form_columns=["id", "test"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model/")
        assert rv.status_code == 200

        rv = client.post("/admin/model/new/", data=dict(id="test1", test="test2"))
        assert rv.status_code == 302

        rv = client.get("/admin/model/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1" in data

        rv = client.get("/admin/model/edit/?id=test1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2" in data


def test_form_columns(app, db, admin):
    with app.app_context():

        class Model(db.Model):
            id = db.Column(db.String, primary_key=True)
            int_field = db.Column(db.Integer)
            datetime_field = db.Column(db.DateTime)
            text_field = db.Column(db.UnicodeText)
            excluded_column = db.Column(db.String)

        class ChildModel(db.Model):
            class EnumChoices(enum.Enum):
                first = 1
                second = 2

            id = db.Column(db.String, primary_key=True)
            model_id = db.Column(db.Integer, db.ForeignKey(Model.id))
            model = db.relationship(Model, backref="backref")
            enum_field = db.Column(db.Enum("model1_v1", "model1_v2"), nullable=True)
            choice_field = db.Column(db.String, nullable=True)
            sqla_utils_choice = db.Column(
                ChoiceType(
                    [("choice-1", "First choice"), ("choice-2", "Second choice")]
                )
            )
            sqla_utils_enum = db.Column(ChoiceType(EnumChoices, impl=db.Integer()))

        db.create_all()

        view1 = CustomModelView(
            Model,
            db.session,
            endpoint="view1",
            form_columns=("int_field", "text_field"),
        )
        view2 = CustomModelView(
            Model,
            db.session,
            endpoint="view2",
            form_excluded_columns=("excluded_column",),
        )
        view3 = CustomModelView(ChildModel, db.session, endpoint="view3")

        form1 = view1.create_form()
        form2 = view2.create_form()
        form3 = view3.create_form()

        assert "int_field" in form1._fields
        assert "text_field" in form1._fields
        assert "datetime_field" not in form1._fields
        assert "excluded_column" not in form2._fields

        # check that relation shows up as a query select
        assert type(form3.model).__name__ == "QuerySelectField"

        # check that select field is rendered if form_choices were specified
        assert type(form3.choice_field).__name__ == "Select2Field"

        # check that select field is rendered for enum fields
        assert type(form3.enum_field).__name__ == "Select2Field"

        # check that sqlalchemy_utils field types are handled appropriately
        assert type(form3.sqla_utils_choice).__name__ == "Select2Field"
        assert type(form3.sqla_utils_enum).__name__ == "Select2Field"

        # test form_columns with model objects
        view4 = CustomModelView(
            Model, db.session, endpoint="view1", form_columns=[Model.int_field]
        )
        form4 = view4.create_form()
        assert "int_field" in form4._fields


@pytest.mark.xfail(raises=Exception)
def test_complex_form_columns(app, db, admin):
    with app.app_context():
        M1, M2 = create_models(db)

        # test using a form column in another table
        view = CustomModelView(M2, db.session, form_columns=["model1.test1"])
        view.create_form()


def test_form_args(app, db, admin):
    with app.app_context():

        class Model(db.Model):
            id = db.Column(db.String, primary_key=True)
            test = db.Column(db.String, nullable=False)

        db.create_all()

        shared_form_args = {"test": {"validators": [validators.Regexp("test")]}}

        view = CustomModelView(Model, db.session, form_args=shared_form_args)
        admin.add_view(view)

        create_form = view.create_form()
        assert len(create_form.test.validators) == 2

        # ensure shared field_args don't create duplicate validators
        edit_form = view.edit_form()
        assert len(edit_form.test.validators) == 2


def test_form_override(app, db, admin):
    with app.app_context():

        class Model(db.Model):
            id = db.Column(db.String, primary_key=True)
            test = db.Column(db.String)

        db.create_all()

        view1 = CustomModelView(Model, db.session, endpoint="view1")
        view2 = CustomModelView(
            Model,
            db.session,
            endpoint="view2",
            form_overrides=dict(test=fields.FileField),
        )
        admin.add_view(view1)
        admin.add_view(view2)

        assert view1._create_form_class.test.field_class == fields.StringField
        assert view2._create_form_class.test.field_class == fields.FileField


def test_form_onetoone(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            test = db.Column(db.String)

        class Model2(db.Model):
            id = db.Column(db.Integer, primary_key=True)

            model1_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
            model1 = db.relationship(
                Model1, backref=db.backref("model2", uselist=False)
            )

        db.create_all()

        view1 = CustomModelView(Model1, db.session, endpoint="view1")
        view2 = CustomModelView(Model2, db.session, endpoint="view2")
        admin.add_view(view1)
        admin.add_view(view2)

        model1 = Model1(test="test")
        model2 = Model2(model1=model1)
        db.session.add(model1)
        db.session.add(model2)
        db.session.commit()

        assert model1.model2 == model2
        assert model2.model1 == model1

        assert not view1._create_form_class.model2.field_class.widget.multiple
        assert not view2._create_form_class.model1.field_class.widget.multiple


def test_relations():
    # TODO: test relations
    pass


def test_on_model_change_delete(app, db, admin):
    with app.app_context():
        Model1, _ = create_models(db)

        class ModelView(CustomModelView):
            def on_model_change(self, form, model, is_created):
                model.test1 = model.test1.upper()

            def on_model_delete(self, model):
                self.deleted = True

        view = ModelView(Model1, db.session)
        admin.add_view(view)

        client = app.test_client()

        client.post("/admin/model1/new/", data=dict(test1="test1large", test2="test2"))

        model = db.session.query(Model1).first()
        assert model.test1 == "TEST1LARGE"

        url = f"/admin/model1/edit/?id={model.id}"
        client.post(url, data=dict(test1="test1small", test2="test2large"))

        model = db.session.query(Model1).first()
        assert model.test1 == "TEST1SMALL"

        url = f"/admin/model1/delete/?id={model.id}"
        client.post(url)
        assert view.deleted


def test_multiple_delete(app, db, admin):
    with app.app_context():
        M1, _ = create_models(db)

        db.session.add_all([M1("a"), M1("b"), M1("c")])
        db.session.commit()
        assert M1.query.count() == 3

        view = ModelView(M1, db.session)
        admin.add_view(view)

        client = app.test_client()

        rv = client.post(
            "/admin/model1/action/", data=dict(action="delete", rowid=[1, 2, 3])
        )
        assert rv.status_code == 302
        assert M1.query.count() == 0


def test_default_sort(app, db, admin):
    with app.app_context():
        M1, _ = create_models(db)

        db.session.add_all([M1("c", "x"), M1("b", "x"), M1("a", "y")])
        db.session.commit()
        assert M1.query.count() == 3

        view = CustomModelView(M1, db.session, column_default_sort="test1")
        admin.add_view(view)

        _, data = view.get_list(0, None, None, None, None)

        assert len(data) == 3
        assert data[0].test1 == "a"
        assert data[1].test1 == "b"
        assert data[2].test1 == "c"

        # test default sort on renamed columns - with column_list scaffolding
        view2 = CustomModelView(
            M1,
            db.session,
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
            db.session,
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
            M1, db.session, column_default_sort=order, endpoint="m1_4"
        )
        admin.add_view(view4)

        _, data = view4.get_list(0, None, None, None, None)

        assert len(data) == 3
        assert data[0].test1 == "b"
        assert data[1].test1 == "c"
        assert data[2].test1 == "a"


def test_complex_sort(app, db, admin):
    with app.app_context():
        M1, M2 = create_models(db)

        m1 = M1(test1="c", test2="x")
        db.session.add(m1)
        db.session.add(M2("c", model1=m1))

        m2 = M1(test1="b", test2="x")
        db.session.add(m2)
        db.session.add(M2("b", model1=m2))

        m3 = M1(test1="a", test2="y")
        db.session.add(m3)
        db.session.add(M2("a", model1=m3))

        db.session.commit()

        # test sorting on relation string - 'model1.test1'
        view = CustomModelView(
            M2,
            db.session,
            column_list=["string_field", "model1.test1"],
            column_sortable_list=["model1.test1"],
        )
        admin.add_view(view)
        view2 = CustomModelView(
            M2,
            db.session,
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


@pytest.mark.xfail(raises=Exception)
def test_complex_sort_exception(app, db, admin):
    with app.app_context():
        M1, M2 = create_models(db)

        # test column_sortable_list on a related table's column object
        view = CustomModelView(
            M2, db.session, endpoint="model2_3", column_sortable_list=[M1.test1]
        )
        admin.add_view(view)

        sort_column = view._get_column_by_idx(0)[0]
        _, data = view.get_list(0, sort_column, False, None, None)

        assert len(data) == 2
        assert data[0].model1.test1 == "a"
        assert data[1].model1.test1 == "b"


def test_default_complex_sort(app, db, admin):
    with app.app_context():
        M1, M2 = create_models(db)

        m1 = M1("b")
        db.session.add(m1)
        db.session.add(M2("c", model1=m1))

        m2 = M1("a")
        db.session.add(m2)
        db.session.add(M2("c", model1=m2))

        db.session.commit()

        view = CustomModelView(M2, db.session, column_default_sort="model1.test1")
        admin.add_view(view)

        _, data = view.get_list(0, None, None, None, None)

        assert len(data) == 2
        assert data[0].model1.test1 == "a"
        assert data[1].model1.test1 == "b"

        # test column_default_sort on a related table's column object
        view2 = CustomModelView(
            M2, db.session, endpoint="model2_2", column_default_sort=(M1.test1, False)
        )
        admin.add_view(view2)

        _, data = view2.get_list(0, None, None, None, None)

        assert len(data) == 2
        assert data[0].model1.test1 == "a"
        assert data[1].model1.test1 == "b"


@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
def test_extra_fields(app, db, admin):
    with app.app_context():
        Model1, _ = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
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


def test_extra_field_order(app, db, admin):
    with app.app_context():
        Model1, _ = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
            form_columns=("extra_field", "test1"),
            form_extra_fields={"extra_field": fields.StringField("Extra Field")},
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        # Check presence and order
        data = rv.data.decode("utf-8")
        pos1 = data.find("Extra Field")
        pos2 = data.find("Test1")
        assert pos2 > pos1


@pytest.mark.parametrize(
    "locale, expect_text",
    (
        ("en", "Home"),
        ("cs", "Domů"),
        ("de", "Start"),
        ("es", "Inicio"),
        ("fa", "خانه"),
        ("fr", "Accueil"),
        ("pt", "Início"),
        ("ru", "Главная"),
        ("pa", "ਹੋਮ"),
        ("zh_CN", "首页"),
        ("zh_TW", "首頁"),
    ),
)
@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
@flask_babel_test_decorator
def test_modelview_localization(request, app, locale, expect_text):
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config["BABEL_DEFAULT_LOCALE"] = locale
    db = request.getfixturevalue("db")
    admin = request.getfixturevalue("admin")

    with app.app_context():
        Model1, _ = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
            column_filters=[
                "test1",
                "bool_field",
                "date_field",
                "datetime_field",
                "time_field",
            ],
        )

        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/")
        assert expect_text in rv.text
        assert rv.status_code == 200

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200


@flask_babel_test_decorator
def test_modelview_named_filter_localization(request, app):
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config["BABEL_DEFAULT_LOCALE"] = "de"
    db = request.getfixturevalue("db")
    _ = request.getfixturevalue("admin")

    with app.app_context():
        Model1, _ = create_models(db)

        view = CustomModelView(
            Model1,
            db.session,
            named_filter_urls=True,
            column_filters=["test1"],
        )

        filters = view.get_filters()
        flt = filters[2]
        with app.test_request_context():
            flt_name = view.get_filter_arg(2, flt)
        assert "test1_equals" == flt_name


def test_custom_form_base(app, db, admin):
    with app.app_context():

        class TestForm(form.BaseForm):
            pass

        Model1, _ = create_models(db)

        view = CustomModelView(Model1, db.session, form_base_class=TestForm)
        admin.add_view(view)

        assert hasattr(view._create_form_class, "test1")

        create_form = view.create_form()
        assert isinstance(create_form, TestForm)


def test_ajax_fk(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        view = CustomModelView(
            Model2,
            db.session,
            url="view",
            form_ajax_refs={"model1": {"fields": ("test1", "test2")}},
        )
        admin.add_view(view)

        assert "model1" in view._form_ajax_refs

        model = Model1("first")
        model2 = Model1("foo", "bar")
        db.session.add_all([model, model2])
        db.session.commit()

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
                f'data-json="[{model.id}, &quot;first&quot;]"' in form.model1()
                or f'data-json="[{model.id}, &#34;first&#34;]"' in form.model1()
            )
            assert 'value="1"' in form.model1()

        # Check querying
        client = app.test_client()

        req = client.get("/admin/view/ajax/lookup/?name=model1&query=foo")
        assert req.data.decode("utf-8") == f'[[{model2.id}, "foo"]]'

        # Check submitting
        req = client.post("/admin/view/new/", data={"model1": as_unicode(model.id)})
        mdl = db.session.query(Model2).first()

        assert mdl is not None
        assert mdl.model1 is not None
        assert mdl.model1.id == model.id
        assert mdl.model1.test1 == "first"


def test_ajax_fk_multi(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            __tablename__ = "model1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(20))

            def __str__(self):
                return self.name

        table = db.Table(
            "m2m",
            db.Model.metadata,
            db.Column("model1_id", db.Integer, db.ForeignKey("model1.id")),
            db.Column("model2_id", db.Integer, db.ForeignKey("model2.id")),
        )

        class Model2(db.Model):
            __tablename__ = "model2"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(20))

            model1_id = db.Column(db.Integer(), db.ForeignKey(Model1.id))
            model1 = db.relationship(Model1, backref="models2", secondary=table)

        db.create_all()

        view = CustomModelView(
            Model2,
            db.session,
            url="view",
            form_ajax_refs={"model1": {"fields": ["name"]}},
        )
        admin.add_view(view)

        assert "model1" in view._form_ajax_refs

        model = Model1(name="first")
        db.session.add_all([model, Model1(name="foo")])
        db.session.commit()

        # Check form generation
        form = view.create_form()
        assert form.model1.__class__.__name__ == "AjaxSelectMultipleField"

        with app.test_request_context("/admin/view/"):
            assert 'data-json="[]"' in form.model1()

            form.model1.data = [model]
            assert (
                'data-json="[[1, &quot;first&quot;]]"' in form.model1()
                or 'data-json="[[1, &#34;first&#34;]]"' in form.model1()
            )

        # Check submitting
        client = app.test_client()
        client.post("/admin/view/new/", data={"model1": as_unicode(model.id)})
        mdl = db.session.query(Model2).first()

        assert mdl is not None
        assert mdl.model1 is not None
        assert len(mdl.model1) == 1


def test_safe_redirect(app, db, admin):
    with app.app_context():
        Model1, _ = create_models(db)

        view = CustomModelView(Model1, db.session)
        admin.add_view(view)

        client = app.test_client()

        rv = client.post(
            "/admin/model1/new/?url=http://localhost/admin/model2view/",
            data=dict(
                test1="test1large",
                test2="test2",
                _continue_editing="Save and Continue Editing",
            ),
        )

        assert rv.status_code == 302

        # werkzeug 2.1.0+ now returns *relative* redirect/location by default.
        expected = "/admin/model1/edit/"

        # handle old werkzeug (or if relative location is disabled via
        # `autocorrect_location_header=True`)
        if (
            not hasattr(rv, "autocorrect_location_header")
            or rv.autocorrect_location_header
        ):
            expected = "http://localhost" + expected

        assert rv.location.startswith(expected)
        assert "url=http://localhost/admin/model2view/" in rv.location
        assert "id=1" in rv.location

        rv = client.post(
            "/admin/model1/new/?url=http://google.com/evil/",
            data=dict(
                test1="test1large",
                test2="test2",
                _continue_editing="Save and Continue Editing",
            ),
        )

        assert rv.status_code == 302
        assert rv.location.startswith(expected)
        assert "url=/admin/model1/" in rv.location
        assert "id=2" in rv.location


def test_simple_list_pager(app, db, admin):
    with app.app_context():
        Model1, _ = create_models(db)

        class TestModelView(CustomModelView):
            simple_list_pager = True

            def get_count_query(self):
                raise AssertionError()

        view = TestModelView(Model1, db.session)
        admin.add_view(view)

        count, data = view.get_list(0, None, None, None, None)
        assert count is None


def test_customising_page_size(app, db, admin):
    with app.app_context():
        M1, _ = create_models(db)

        db.session.add_all([M1(str(f"instance-{x+1:03d}")) for x in range(101)])

        view1 = CustomModelView(
            M1, db.session, endpoint="view1", page_size=20, can_set_page_size=False
        )
        admin.add_view(view1)

        view2 = CustomModelView(
            M1, db.session, endpoint="view2", page_size=5, can_set_page_size=False
        )
        admin.add_view(view2)

        view3 = CustomModelView(
            M1, db.session, endpoint="view3", page_size=20, can_set_page_size=True
        )
        admin.add_view(view3)

        view4 = CustomModelView(
            M1,
            db.session,
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


def test_unlimited_page_size(app, db, admin):
    with app.app_context():
        M1, _ = create_models(db)

        db.session.add_all(
            [
                M1("1"),
                M1("2"),
                M1("3"),
                M1("4"),
                M1("5"),
                M1("6"),
                M1("7"),
                M1("8"),
                M1("9"),
                M1("10"),
                M1("11"),
                M1("12"),
                M1("13"),
                M1("14"),
                M1("15"),
                M1("16"),
                M1("17"),
                M1("18"),
                M1("19"),
                M1("20"),
                M1("21"),
            ]
        )

        view = CustomModelView(M1, db.session)

        # test 0 as page_size
        _, data = view.get_list(0, None, None, None, None, execute=True, page_size=0)
        assert len(data) == 21

        # test False as page_size
        _, data = view.get_list(
            0, None, None, None, None, execute=True, page_size=False
        )
        assert len(data) == 21


def test_advanced_joins(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val1 = db.Column(db.String(20))
            test = db.Column(db.String(20))

        class Model2(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val2 = db.Column(db.String(20))

            model1_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
            model1 = db.relationship(Model1, backref="model2")

        class Model3(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val2 = db.Column(db.String(20))

            model2_id = db.Column(db.Integer, db.ForeignKey(Model2.id))
            model2 = db.relationship(Model2, backref="model3")

        view1 = CustomModelView(Model1, db.session)
        admin.add_view(view1)

        view2 = CustomModelView(Model2, db.session)
        admin.add_view(view2)

        view3 = CustomModelView(Model3, db.session)
        admin.add_view(view3)

        # Test joins
        attr, path = tools.get_field_with_path(Model2, "model1.val1")
        assert attr == Model1.val1
        assert path == [Model2.model1]

        attr, path = tools.get_field_with_path(Model1, "model2.val2")
        assert attr == Model2.val2
        assert id(path[0]) == id(Model1.model2)

        attr, path = tools.get_field_with_path(Model3, "model2.model1.val1")
        assert attr == Model1.val1
        assert path == [Model3.model2, Model2.model1]

        # Test how joins are applied
        query = view3.get_query()

        joins = {}
        q1, joins, alias = view3._apply_path_joins(query, joins, path)
        assert (True, Model3.model2) in joins
        assert (True, Model2.model1) in joins
        assert alias is not None

        # Check if another join would use same path
        attr, path = tools.get_field_with_path(Model2, "model1.test")
        q2, joins, alias = view2._apply_path_joins(query, joins, path)

        assert len(joins) == 2

        if hasattr(q2, "_join_entities"):
            for p in q2._join_entities:
                assert p in q1._join_entities

        assert alias is not None

        # Check if normal properties are supported by tools.get_field_with_path
        attr, path = tools.get_field_with_path(Model2, Model1.test)
        assert attr == Model1.test
        assert path == [Model1.__table__]

        q3, joins, alias = view2._apply_path_joins(view2.get_query(), joins, path)
        assert len(joins) == 3
        assert alias is None


def test_multipath_joins(app, db, admin):
    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val1 = db.Column(db.String(20))
            test = db.Column(db.String(20))

        class Model2(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val2 = db.Column(db.String(20))

            first_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
            first = db.relationship(Model1, backref="first", foreign_keys=[first_id])

            second_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
            second = db.relationship(Model1, backref="second", foreign_keys=[second_id])

        db.create_all()

        view = CustomModelView(Model2, db.session, filters=["first.test"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200


def test_different_bind_joins(request, app):
    app.config["SQLALCHEMY_BINDS"] = {"other": "sqlite:///"}

    db = request.getfixturevalue("db")
    admin = request.getfixturevalue("admin")

    with app.app_context():

        class Model1(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            val1 = db.Column(db.String(20))

        class Model2(db.Model):
            __bind_key__ = "other"
            id = db.Column(db.Integer, primary_key=True)
            val1 = db.Column(db.String(20))
            first_id = db.Column(db.Integer, db.ForeignKey(Model1.id))
            first = db.relationship(Model1)

        db.create_all()

        view = CustomModelView(Model2, db.session)
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200


def test_model_default(app, db, admin):
    with app.app_context():
        _, Model2 = create_models(db)

        class ModelView(CustomModelView):
            pass

        view = ModelView(Model2, db.session)
        admin.add_view(view)

        client = app.test_client()
        rv = client.post("/admin/model2/new/", data=dict())
        assert b"This field is required" not in rv.data


def test_export_csv(app, db, admin):
    with app.app_context():
        Model1, Model2 = create_models(db)

        for _x in range(5):
            fill_db(db, Model1, Model2)

        view1 = CustomModelView(
            Model1,
            db.session,
            can_export=True,
            column_list=["test1", "test2"],
            export_max_rows=2,
            endpoint="row_limit_2",
        )
        admin.add_view(view1)
        view2 = CustomModelView(
            Model1,
            db.session,
            can_export=True,
            column_list=["test1", "test2"],
            endpoint="no_row_limit",
        )
        admin.add_view(view2)

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


STRING_CONSTANT = "Anyway, here's Wonderwall"


def test_string_null_behavior(app, db, admin):
    with app.app_context():

        class StringTestModel(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            test_no = db.Column(db.Integer, nullable=False)
            string_field = db.Column(db.String)
            string_field_nonull = db.Column(db.String, nullable=False)
            string_field_nonull_default = db.Column(
                db.String, nullable=False, default=""
            )
            text_field = db.Column(db.Text)
            text_field_nonull = db.Column(db.Text, nullable=False)
            text_field_nonull_default = db.Column(db.Text, nullable=False, default="")

        db.create_all()

        view = CustomModelView(StringTestModel, db.session)
        admin.add_view(view)

        client = app.test_client()

        valid_params = {
            "test_no": 1,
            "string_field_nonull": STRING_CONSTANT,
            "text_field_nonull": STRING_CONSTANT,
        }
        rv = client.post("/admin/stringtestmodel/new/", data=valid_params)
        assert rv.status_code == 302

        # Assert on defaults
        valid_inst = (
            db.session.query(StringTestModel).filter(StringTestModel.test_no == 1).one()
        )
        assert valid_inst.string_field is None
        assert valid_inst.string_field_nonull == STRING_CONSTANT
        assert valid_inst.string_field_nonull_default == ""
        assert valid_inst.text_field is None
        assert valid_inst.text_field_nonull == STRING_CONSTANT
        assert valid_inst.text_field_nonull_default == ""

        # Assert that nulls are caught on the non-null fields
        invalid_string_field = {
            "test_no": 2,
            "string_field_nonull": None,
            "text_field_nonull": STRING_CONSTANT,
        }
        rv = client.post("/admin/stringtestmodel/new/", data=invalid_string_field)
        assert rv.status_code == 200
        assert b"This field is required." in rv.data
        assert (
            db.session.query(StringTestModel).filter(StringTestModel.test_no == 2).all()
            == []
        )

        invalid_text_field = {
            "test_no": 3,
            "string_field_nonull": STRING_CONSTANT,
            "text_field_nonull": None,
        }
        rv = client.post("/admin/stringtestmodel/new/", data=invalid_text_field)
        assert rv.status_code == 200
        assert b"This field is required." in rv.data
        assert (
            db.session.query(StringTestModel).filter(StringTestModel.test_no == 3).all()
            == []
        )

        # Assert that empty strings are converted to None on nullable fields.
        empty_strings = {
            "test_no": 4,
            "string_field": "",
            "text_field": "",
            "string_field_nonull": STRING_CONSTANT,
            "text_field_nonull": STRING_CONSTANT,
        }
        rv = client.post("/admin/stringtestmodel/new/", data=empty_strings)
        assert rv.status_code == 302
        empty_string_inst = (
            db.session.query(StringTestModel).filter(StringTestModel.test_no == 4).one()
        )
        assert empty_string_inst.string_field is None
        assert empty_string_inst.text_field is None
