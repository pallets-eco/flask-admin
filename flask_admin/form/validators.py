from wtforms import FieldList
from wtforms import Form
from wtforms.validators import StopValidation

from flask_admin.babel import gettext


class FieldListInputRequired:
    """
    Validates that at least one item was provided for a FieldList
    """

    field_flags = {"required": True}

    def __call__(self, form: Form, field: FieldList) -> None:
        if len(field.entries) == 0:
            field.errors[:] = []  # type:ignore[index]
            raise StopValidation(gettext("This field requires at least one item."))
