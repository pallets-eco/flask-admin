import inspect
from unittest.mock import MagicMock

import pytest
import wtforms
from wtforms.fields.simple import StringField

from flask_admin.contrib.sqla.form import AdminModelConverter

# Get all converter methods from AdminModelConverter
sqla_admin_model_converters = [
    method_name
    for method_name, method in inspect.getmembers(AdminModelConverter)
    if getattr(method, "_converter_for", None)
]


class TestAdminModelConverter:
    @pytest.mark.parametrize("method_name", sqla_admin_model_converters)
    def test_can_override_widget(self, method_name):
        # Simulate your SQLModelView converter
        converter = AdminModelConverter(None, None)

        def fake_widget(*args, **kwargs):
            return "<p>widget overridden</p>"

        class TestForm(wtforms.Form):
            pass

        argspec = inspect.signature(StringField.__init__).parameters
        name_field = "name" if "name" in argspec else "_name"

        field_args = {
            "_form": TestForm(),
            name_field: "field",
            "widget": fake_widget,
            "validators": [],
        }

        # Convert field using one of the converter methods
        field = getattr(converter, method_name)(
            field_args=field_args,
            column=MagicMock(),
        )

        try:
            field.data = None
        except AttributeError:
            pass

        assert field() == "<p>widget overridden</p>"












