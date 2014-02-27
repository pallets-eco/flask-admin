from re import sub
from jinja2 import contextfunction
from flask import g, request
from wtforms.validators import DataRequired, InputRequired

from flask.ext.admin._compat import urljoin, urlparse


from ._compat import string_types


def set_current_view(view):
    g._admin_view = view


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
        Check if wtforms field has error without checking its children.

        :param errors:
            Errors list.
    """
    for e in errors:
        if isinstance(e, string_types):
            return True

    return False


@contextfunction
def resolve_ctx(context):
    """
        Resolve current Jinja2 context and store it for general consumption.
    """
    g._admin_render_ctx = context


def get_render_ctx():
    """
        Get view template context.
    """
    return getattr(g, '_admin_render_ctx', None)


def prettify_class_name(name):
    """
        Split words in PascalCase string into separate words.

        :param name:
            String to split
    """
    return sub(r'(?<=.)([A-Z])', r' \1', name)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)


def get_redirect_target(param_name='url'):
    target = request.values.get(param_name)

    if target and is_safe_url(target):
        return target
