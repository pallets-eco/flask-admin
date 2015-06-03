from re import sub
from jinja2 import contextfunction
from flask import g, request, url_for, flash
from wtforms.validators import DataRequired, InputRequired

from flask_admin._compat import urljoin, urlparse, iteritems

from ._compat import string_types


def set_current_view(view):
    g._admin_view = view


def get_current_view():
    """
        Get current administrative view.
    """
    return getattr(g, '_admin_view', None)


def get_url(endpoint, **kwargs):
    """
        Alternative to Flask `url_for`.
        If there's current administrative view, will call its `get_url`. If there's none - will
        use generic `url_for`.

        :param endpoint:
            Endpoint name
        :param kwargs:
            View arguments
    """
    view = get_current_view()

    if not view:
        return url_for(endpoint, **kwargs)

    return view.get_url(endpoint, **kwargs)


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
    return request and request.method in ('PUT', 'POST')


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
    if isinstance(errors, (list, tuple)):
        for e in errors:
            if isinstance(e, string_types):
                return True

    return False


def flash_errors(form, message):
    from flask_admin.babel import gettext
    for field_name, errors in iteritems(form.errors):
        errors = form[field_name].label.text + u": " + u", ".join(errors)
        flash(gettext(message, error=str(errors)), 'error')

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
