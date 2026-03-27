import enum
import inspect
import typing as t
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils
import wtforms
from wtforms.fields.simple import StringField
from wtforms.validators import Length
from wtforms.validators import NumberRange

from flask_admin.contrib.sqla.form import AdminModelConverter
from flask_admin.tests.conftest import skip_or_return_session_or_db
from flask_admin.tests.sqla.test_basic import CustomModelView

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


class EnumChoices(enum.Enum):
    first = 101
    second = 150


class StrEnumChoices(enum.Enum):
    first = "101"
    second = "150"


def create_models(sqla_db_ext):
    class Model1(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "model1"

        def __init__(self, test1, int_field):
            self.test1 = test1
            self.int_field = int_field

        id = sa.Column(sa.Integer, primary_key=True)
        test1 = sa.Column(sa.String(20))
        int_field = sa.Column(sa.Integer)
        float_field = sa.Column(sa.Float)
        choice_field = sa.Column(sa.String, nullable=True)
        enum_field = sa.Column(sa.Enum("101", "150"), nullable=True)  # type: ignore[var-annotated]
        enum_type_field = sa.Column(sa.Enum(EnumChoices), nullable=True)  # type: ignore[var-annotated]
        sa_utils_choicetype = sa.Column(
            sa_utils.ChoiceType(
                [("101", "First"), ("150", "Second")]
            )  # default impl=sa.String()
        )
        sa_utils_choicetype_impl_int = sa.Column(
            sa_utils.ChoiceType([(101, "First"), (150, "Second")], impl=sa.Integer())
        )
        sa_utils_choicetype_with_enum = sa.Column(
            sa_utils.ChoiceType(EnumChoices, impl=sa.Integer())
        )
        sa_utils_choicetype_with_strenum = sa.Column(
            sa_utils.ChoiceType(StrEnumChoices, impl=sa.String())
        )

        def __str__(self):
            return self.test1

    sqla_db_ext.create_all()

    return Model1


@pytest.mark.parametrize("use_coerce_explicitly", [True, False])
@pytest.mark.parametrize(
    "field_name, expected_coerce",
    [
        ("int_field", int),
        ("float_field", float),
        ("choice_field", str),
        ("enum_field", str),
        ("sa_utils_choicetype", str),
        ("sa_utils_choicetype_impl_int", int),
    ],
)
def test_coerce(
    app,
    admin,
    sqla_db_ext,
    session_or_db,
    field_name,
    expected_coerce,
    use_coerce_explicitly,
):
    with app.app_context():
        Model1 = create_models(sqla_db_ext)
        sqla_db_ext.db.session.add_all(
            [
                Model1("101", int_field=101),
                Model1("102", int_field=102),
            ]
        )
        sqla_db_ext.db.session.commit()

        validators: list[t.Any] = []
        if expected_coerce in [int, float]:
            validators = [NumberRange(min=100, max=199)]
        elif expected_coerce in [str]:
            validators = [Length(min=1, max=3)]

        f_choices = [(expected_coerce(101), "First"), (expected_coerce(150), "Second")]

        kwargs = {
            "form_columns": [field_name],
            "form_choices": {field_name: f_choices},
        }

        if use_coerce_explicitly:
            kwargs["form_args"] = {}
            kwargs["form_args"][field_name] = {"validators": validators}  # type: ignore[index]
            kwargs["form_args"][field_name]["coerce"] = expected_coerce  # type: ignore[index]

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)

        view1 = CustomModelView(Model1, param, name="My Model1", **kwargs)
        admin.add_view(view1)

    client = app.test_client()
    rv = client.get("/admin/model1/new/")
    data = rv.data.decode("utf-8")
    assert f'value="{expected_coerce(101)}"' in data
    assert ">First</option>" in data

    rv = client.post(
        "/admin/model1/new/",
        data={field_name: f"{expected_coerce(150)}"},
        follow_redirects=True,
    )
    data = rv.data.decode("utf-8")
    assert "Record was successfully created" in data


@pytest.mark.parametrize("use_coerce_explicitly", [True, False])
@pytest.mark.parametrize(
    "field_name, expected_coerce",
    [
        ("enum_type_field", EnumChoices),
        ("sa_utils_choicetype_with_enum", EnumChoices),
        ("sa_utils_choicetype_with_strenum", StrEnumChoices),
    ],
)
def test_str_coerce(
    app,
    admin,
    sqla_db_ext,
    session_or_db,
    field_name,
    expected_coerce,
    use_coerce_explicitly,
):
    with app.app_context():
        Model1 = create_models(sqla_db_ext)
        sqla_db_ext.db.session.add_all(
            [
                Model1("101", int_field=101),
                Model1("102", int_field=102),
            ]
        )
        sqla_db_ext.db.session.commit()

        f_choices = [
            (expected_coerce["first"], "First"),
            (expected_coerce["second"], "Second"),
        ]

        kwargs = {
            "form_columns": [field_name],
            "form_choices": {field_name: f_choices},
        }

        if use_coerce_explicitly:
            kwargs["form_args"] = {}
            kwargs["form_args"][field_name] = {}  # type: ignore[index]
            kwargs["form_args"][field_name]["coerce"] = expected_coerce  # type: ignore[index]

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)

        view1 = CustomModelView(Model1, param, name="My Model1", **kwargs)
        admin.add_view(view1)

    client = app.test_client()
    rv = client.get("/admin/model1/new/")
    data = rv.data.decode("utf-8")
    assert f'value="{expected_coerce["first"]}"' in data
    assert ">First</option>" in data

    rv = client.post(
        "/admin/model1/new/",
        data={field_name: f"{expected_coerce['second']}"},
        follow_redirects=True,
    )
    data = rv.data.decode("utf-8")
    assert "Record was successfully created" in data
