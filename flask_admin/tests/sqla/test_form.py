import inspect
import typing as t
from unittest.mock import MagicMock

import pytest
import wtforms
from sqlalchemy import ARRAY
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from wtforms.fields.simple import StringField

from flask_admin.contrib.sqla.form import AdminModelConverter

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
