import jinja2
from flask import g, request
from wtforms.validators import DataRequired, InputRequired

from ._compat import string_types


def set_current_view(view):
    g._admin_view = view


@jinja2.contextfunction
def get_context(c):
    return c


def get_current_view():
    """
        Get current administrative view.
    """
    return getattr(g, '_admin_view', None)


def is_required_form_field(field):
    """
        Check if form field has `DataRequired` or `InputRequired` validators.

        :param field:
            WTForms field to check
    """
    for validator in field.validators:
        if isinstance(validator, (DataRequired, InputRequired)):
            return True
    return False


def is_form_submitted():
    """
        Check if current method is PUT or POST
    """
    return request and request.method in ("PUT", "POST")


def validate_form_on_submit(form):
    """
        If current method is PUT or POST, validate form and return validation status.
    """
    return is_form_submitted() and form.validate()


def get_form_data():
    """
        If current method is PUT or POST, return concatenated `request.form` with
        `request.files` or `None` otherwise.
    """
    if is_form_submitted():
        formdata = request.form
        if request.files:
            formdata = formdata.copy()
            formdata.update(request.files)
        return formdata

    return None


def is_field_error(errors):
    """
        Check if wtforms field has direct error.

        :param errors:
            Errors list.
    """
    for e in errors:
        if isinstance(e, string_types):
            return True

    return False
