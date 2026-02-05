import inspect
from unittest.mock import MagicMock

import pytest
import wtforms
from wtforms.fields.simple import StringField
from wtforms.validators import NumberRange

from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.form import AdminModelConverter
from flask_admin.tests.sqla.test_basic import create_models

sqla_admin_model_converters = [
    method_name
    for method_name, method in inspect.getmembers(AdminModelConverter)
    if getattr(method, "_converter_for", None)
]


class TestAdminModelConverter:
    @pytest.mark.parametrize("method_name", sqla_admin_model_converters)
    def test_can_override_widget(self, method_name):
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]

        def fake_widget(*args, **kwargs):
            return "<p>widget overridden</p>"

        class TestForm(wtforms.Form):
            pass

        # Find out if field takes `name` or `_name` - depends on wtforms version.
        # Required for python3.8 tests
        argspec = inspect.signature(StringField.__init__).parameters
        name_field = "name" if "name" in argspec else "_name"

        # Build args to pass to wtforms Field instance - mostly fake data, the only
        # important thing is the fake widget. `_form` and name_field are required
        # to get a 'bound' field instance that can be rendered.
        field_args = {
            "_form": TestForm(),
            name_field: "field",
            "widget": fake_widget,
            "validators": [],
        }

        field = getattr(converter, method_name)(
            field_args=field_args,
            column=MagicMock(),
        )

        # Some non-wtforms fields (eg `Select2TagsField` don't allow setting this field
        try:
            field.data = None
        except AttributeError:
            pass

        assert field() == "<p>widget overridden</p>"


@pytest.mark.parametrize(
    "session_or_db",
    [
        pytest.param("session"),
        pytest.param("db"),
    ],
)
def test_coerce(app, db, admin, session_or_db):
    with app.app_context():
        Model1, Model2 = create_models(db)
        db.session.add_all(
            [
                Model2("1", int_field=1),
                Model2("2", int_field=2),
            ]
        )
        db.session.commit()

        class MyModelView(ModelView):
            form_columns = ["int_field"]
            form_choices = {"int_field": [(101, "101"), (150, "150")]}
            form_args = {
                "int_field": {"validators": [NumberRange(min=100, max=199)]},
            }

        class MyModelView2(MyModelView):
            form_args = {
                "int_field": {
                    "validators": [NumberRange(min=100, max=199)],
                    "coerce": int,
                },
            }

        param = db if session_or_db == "session" else db.session
        # test column_list with a list of strings
        view1 = MyModelView(Model2, param, name="My Model1")
        view2 = MyModelView2(Model2, param, name="My Model1", endpoint="mymodelview2")
        admin.add_view(view1)
        admin.add_view(view2)

        client = app.test_client()
        rv = client.get("/admin/model2/new/")
        data = rv.data.decode("utf-8")
        assert 'value="101"' in data
        assert ">101</option>" in data

        rv = client.post(
            "/admin/model2/new/", data={"int_field": "150"}, follow_redirects=True
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully created" in data

        rv = client.post(
            "/admin/mymodelview2/new/", data={"int_field": "150"}, follow_redirects=True
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully created" in data
