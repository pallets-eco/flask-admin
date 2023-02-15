from re import sub, compile
from flask import g, request, url_for, flash
from wtforms.validators import DataRequired, InputRequired

from flask_admin._compat import iteritems, pass_context, urljoin, urlparse

from ._compat import string_types


VALID_SCHEMES = ['http', 'https']
_substitute_whitespace = compile(r'[\s\x00-\x08\x0B\x0C\x0E-\x19]+').sub
_fix_multiple_slashes = compile(r'(^([^/]+:)?//)/*').sub


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
        Check if form field has `DataRequired`, `InputRequired`, or
        `FieldListInputRequired` validators.

        :param field:
            WTForms field to check
    """
    from flask_admin.form.validators import FieldListInputRequired
    for validator in field.validators:
        if isinstance(validator, (DataRequired, InputRequired, FieldListInputRequired)):
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


@pass_context
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
    # prevent urls like "\\www.google.com"
    # some browser will change \\ to // (eg: Chrome)
    # refs https://stackoverflow.com/questions/10438008
    target = target.replace('\\', '/')

    # handle cases like "j a v a s c r i p t:"
    target = _substitute_whitespace('', target)

    # Chrome and FireFox "fix" more than two slashes into two after protocol
    target = _fix_multiple_slashes(lambda m: m.group(1), target, 1)

    # prevent urls starting with "javascript:"
    target_info = urlparse(target)
    target_scheme = target_info.scheme
    if target_scheme and target_scheme not in VALID_SCHEMES:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return ref_url.netloc == test_url.netloc


def get_redirect_target(param_name='url'):
    target = request.values.get(param_name)

    if target and is_safe_url(target):
        return target
