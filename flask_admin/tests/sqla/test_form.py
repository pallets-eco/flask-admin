import enum
import inspect
import typing as t
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import sqlalchemy_utils as sau
import wtforms
from flask import Flask
from sqlalchemy import ARRAY
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from wtforms.fields.simple import StringField
from wtforms.validators import Length
from wtforms.validators import NumberRange

from flask_admin.base import Admin
from flask_admin.contrib.sqla.form import AdminModelConverter
from flask_admin.tests.conftest import skip_or_return_session_or_db
from flask_admin.tests.conftest import T_ANY_SQLA_PROVIDER
from flask_admin.tests.conftest import T_LITERAL_SESSION_OR_DB
from flask_admin.tests.sqla.test_basic import CustomModelView

sqla_admin_model_converters = [
    method_name
    for method_name, method in inspect.getmembers(AdminModelConverter)
    if getattr(method, "_converter_for", None)
]


class TestAdminModelConverter:
    @pytest.mark.parametrize("method_name", sqla_admin_model_converters)
    def test_can_override_widget(self, method_name: str) -> None:
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]

        def fake_widget(*args: t.Any, **kwargs: t.Any) -> str:
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


class TestArrayConverter:
    """Regression tests for `AdminModelConverter.conv_ARRAY` -- see issue #1724.

    Without an inner-type-aware coerce callable, every submitted value for a
    Postgres `ARRAY(Integer)` column is sent back to the DB as a Python
    `str`, so the resulting `text[]` value is rejected with
        column "x" is of type integer[] but expression is of type text[]
    The converter now passes a `coerce` derived from the array element's
    `python_type` so the round-trip lines up with the column type.
    """

    def _bind(self, unbound_field: t.Any) -> t.Any:
        """The converter returns a wtforms UnboundField. Bind it onto a real
        form so we can drive `process_formdata` and inspect `.data`.
        """

        class _F(wtforms.Form):
            x = unbound_field

        return _F().x

    def test_conv_ARRAY_integer_coerces_each_item_to_int(self) -> None:
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]
        column: Column[t.Any] = Column("x", ARRAY(Integer))
        bound = self._bind(
            converter.conv_ARRAY(field_args={"validators": []}, column=column)
        )

        bound.process_formdata(["1,2,3"])

        assert bound.data == [1, 2, 3]
        # Hard-pin element types so a future change of the inner coerce can't
        # silently regress to strings.
        assert all(isinstance(v, int) for v in bound.data), bound.data

    def test_conv_ARRAY_float_coerces_each_item_to_float(self) -> None:
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]
        column: Column[t.Any] = Column("x", ARRAY(Float))
        bound = self._bind(
            converter.conv_ARRAY(field_args={"validators": []}, column=column)
        )

        bound.process_formdata(["1.5, 2.0"])

        assert bound.data == [1.5, 2.0]
        assert all(isinstance(v, float) for v in bound.data), bound.data

    def test_conv_ARRAY_string_keeps_string_default(self) -> None:
        """String arrays must continue to work exactly as before -- no
        spurious coercion that would round-trip values through `int()`.
        """
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]
        column: Column[t.Any] = Column("x", ARRAY(String))
        bound = self._bind(
            converter.conv_ARRAY(field_args={"validators": []}, column=column)
        )

        bound.process_formdata(["alpha,beta,gamma"])

        assert bound.data == ["alpha", "beta", "gamma"]

    def test_conv_ARRAY_missing_item_type_falls_back_to_text(self) -> None:
        """If the column object can't be introspected (e.g. legacy callers
        passing a MagicMock), the converter must not raise. The previous
        default (string coerce) is preserved.
        """
        converter = AdminModelConverter(None, None)  # type: ignore[arg-type]
        # MagicMock().type.item_type silently returns another MagicMock, whose
        # python_type access would itself succeed and return a MagicMock --
        # which is precisely the kind of pathological case we need to handle
        # without exploding.
        column = MagicMock()
        # Force item_type to be absent so the fallback branch is exercised.
        column.type.spec_set = ["item_type"]
        del column.type.item_type

        bound = self._bind(
            converter.conv_ARRAY(field_args={"validators": []}, column=column)
        )

        bound.process_formdata(["x,y"])
        assert bound.data == ["x", "y"]


class EnumChoices(enum.Enum):
    First = 101
    Second = 150


class StrEnumChoices(enum.Enum):
    First = "101"
    Second = "150"


def create_models(sqla_db_ext: T_ANY_SQLA_PROVIDER) -> t.Any:
    class Model1(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "model1"

        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        test1 = sa.Column(sa.String(20))
        int_field = sa.Column(sa.Integer)
        float_field = sa.Column(sa.Float)
        choice_field = sa.Column(sa.String, nullable=True)
        enum_field = sa.Column(sa.Enum("101", "150"), nullable=True)  # type: ignore[var-annotated]
        enum_type_field = sa.Column(sa.Enum(EnumChoices), nullable=True)  # type: ignore[var-annotated]
        sau_choicetype = sa.Column(
            sau.ChoiceType(
                [("101", "First"), ("150", "Second")]
            )  # default impl=sa.String()
        )
        sau_choicetype_impl_int = sa.Column(
            sau.ChoiceType([(101, "First"), (150, "Second")], impl=sa.Integer())
        )
        sau_choicetype_with_enum = sa.Column(
            sau.ChoiceType(EnumChoices, impl=sa.Integer())
        )
        sau_choicetype_with_strenum = sa.Column(
            sau.ChoiceType(StrEnumChoices, impl=sa.String())
        )

        def __str__(self) -> str:
            return str(self.test1.value) if self.test1 else ""

    sqla_db_ext.create_all()

    return Model1


def prepare_kwargs(
    expected_coerce: type[t.Any],
    use_coerce_explicitly: bool,
    field_name: str,
) -> dict[str, t.Any]:
    validators: list[t.Any] = []
    kwargs: dict[str, t.Any] = dict()

    if expected_coerce in [int, float]:
        f_choices = [(expected_coerce(101), "First"), (expected_coerce(150), "Second")]
        validators = [NumberRange(min=100, max=199)]
        kwargs["form_choices"] = {field_name: f_choices}

    elif expected_coerce in [
        str,
    ]:
        f_choices = [(expected_coerce(101), "First"), (expected_coerce(150), "Second")]
        validators = [Length(min=1, max=3)]
        kwargs["form_choices"] = {field_name: f_choices}

    elif expected_coerce in [EnumChoices, StrEnumChoices]:
        pass

    kwargs["form_columns"] = [field_name]

    if use_coerce_explicitly:
        kwargs["form_args"] = dict()
        kwargs["form_args"][field_name] = {"validators": validators}
        kwargs["form_args"][field_name]["coerce"] = expected_coerce

    return kwargs


@pytest.mark.parametrize("use_coerce_explicitly", [False, True])
@pytest.mark.parametrize(
    "field_name, expected_coerce, coerced_value, model_value",
    [
        ("int_field", int, None, 101),
        ("float_field", float, None, 101.0),
        ("choice_field", str, None, "101"),
        ("enum_field", str, None, "101"),
        ("enum_type_field", EnumChoices, "First", EnumChoices.First),
        ("sau_choicetype", str, None, sau.Choice("101", "First")),
        ("sau_choicetype_impl_int", int, None, sau.Choice(101, "First")),
        ("sau_choicetype_with_enum", EnumChoices, "101", EnumChoices.First),
        ("sau_choicetype_with_strenum", StrEnumChoices, "101", StrEnumChoices.First),
    ],
)
def test_coerce(
    app: Flask,
    admin: Admin,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    session_or_db: T_LITERAL_SESSION_OR_DB,
    field_name: str,
    expected_coerce: type[t.Any],
    use_coerce_explicitly: bool,
    coerced_value: t.Any,
    model_value: t.Any,
) -> None:
    with app.app_context():
        Model1 = create_models(sqla_db_ext)
        sqla_db_ext.db.session.add_all(
            [
                Model1(test1="101", int_field=101),
                Model1(test1="102", int_field=102),
            ]
        )
        sqla_db_ext.db.session.commit()

        kwargs = prepare_kwargs(expected_coerce, use_coerce_explicitly, field_name)

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)

        view1 = CustomModelView(Model1, param, name="My Model1", **kwargs)
        admin.add_view(view1)

    value = expected_coerce(101) if coerced_value is None else coerced_value

    client = app.test_client()

    rv = client.get("/admin/model1/new/")
    data = rv.data.decode("utf-8")
    assert f'value="{value}"' in data
    assert ">First</option>" in data

    rv = client.post(
        "/admin/model1/new/",
        data={field_name: f"{value}"},
        follow_redirects=True,
    )
    data = rv.data.decode("utf-8")
    assert "Record was successfully created" in data

    inserted = sqla_db_ext.db.session.query(Model1).order_by(Model1.id.desc()).first()
    assert inserted is not None
    assert getattr(inserted, field_name) == model_value
