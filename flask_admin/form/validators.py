from wtforms.validators import StopValidation

from flask_admin.babel import gettext


class FieldListInputRequired:
    """
    Validates that at least one item was provided for a FieldList
    """

    field_flags = {"required": True}

    def __call__(self, form, field):
        if len(field.entries) == 0:
            field.errors[:] = []
            raise StopValidation(gettext("This field requires at least one item."))
