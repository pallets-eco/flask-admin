from flask import g
from wtforms.validators import DataRequired, InputRequired


def set_current_view(view):
    g._admin_view = view


def get_current_view():
    return getattr(g, '_admin_view', None)


def is_required_form_field(field):
    for validator in field.validators:
        if isinstance(validator, (DataRequired, InputRequired)):
            return True
    return False
