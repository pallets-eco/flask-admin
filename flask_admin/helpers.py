import typing as t
from re import compile
from re import sub
from urllib.parse import urljoin
from urllib.parse import urlparse

from flask import current_app
from flask import flash
from flask import g
from flask import request
from flask import url_for
from jinja2 import pass_context  # type: ignore[attr-defined]
from jinja2.runtime import Context
from werkzeug.datastructures import ImmutableMultiDict
from wtforms.fields.core import Field
from wtforms.form import BaseForm
from wtforms.form import Form
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired

from ._compat import iteritems
from ._compat import string_types
from ._types import T_MODEL_VIEW

VALID_SCHEMES = ["http", "https"]
_substitute_whitespace = compile(r"[\s\x00-\x08\x0B\x0C\x0E-\x19]+").sub
_fix_multiple_slashes = compile(r"(^([^/]+:)?//)/*").sub


def set_current_view(view: T_MODEL_VIEW) -> None:
    g._admin_view = view


def get_current_view() -> t.Optional[t.Any]:
    """
    Get current administrative view.
    """
    return getattr(g, "_admin_view", None)


def get_url(endpoint: str, **kwargs: t.Any) -> str:
    """
    Alternative to Flask `url_for`.
    If there's current administrative view, will call its `get_url`. If there's
    none - will use generic `url_for`.

    :param endpoint:
        Endpoint name
    :param kwargs:
        View arguments
    """
    view = get_current_view()

    if not view:
        return url_for(endpoint, **kwargs)

    return view.get_url(endpoint, **kwargs)


def is_required_form_field(field: Field) -> bool:
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


def is_form_submitted() -> bool:
    """
    Check if current method is PUT or POST
    """
    return bool(request and request.method in ("PUT", "POST"))


def validate_form_on_submit(form: Form) -> bool:
    """
    If current method is PUT or POST, validate form and return validation status.
    """
    return is_form_submitted() and form.validate()


def get_form_data() -> t.Optional[ImmutableMultiDict]:
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


def is_field_error(errors: t.Union[list, tuple, None]) -> bool:
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


def flash_errors(form: BaseForm, message: str) -> None:
    from flask_admin.babel import gettext

    for field_name, errors in iteritems(form.errors):
        errors = form[field_name].label.text + ": " + ", ".join(errors)
        flash(gettext(message, error=str(errors)), "error")


@pass_context
def resolve_ctx(context: Context) -> None:
    """
    Resolve current Jinja2 context and store it for general consumption.
    """
    g._admin_render_ctx = context


def get_render_ctx() -> t.Optional[Context]:
    """
    Get view template context.
    """
    return getattr(g, "_admin_render_ctx", None)


def prettify_class_name(name: str) -> str:
    """
    Split words in PascalCase string into separate words.

    :param name:
        String to split
    """
    return sub(r"(?<=.)([A-Z])", r" \1", name)


def is_safe_url(target: str) -> bool:
    # prevent urls like "\\www.google.com"
    # some browser will change \\ to // (eg: Chrome)
    # refs https://stackoverflow.com/questions/10438008
    target = target.replace("\\", "/")

    # handle cases like "j a v a s c r i p t:"
    target = _substitute_whitespace("", target)

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


def get_redirect_target(param_name: str = "url") -> t.Optional[str]:
    target = request.values.get(param_name)

    if target and is_safe_url(target):
        return target
    return None


def get_theme() -> str:
    """
    Gets the theme folder by inspecting the active Admin instance's views.

    This function identifies the correct Admin instance for the current
    request by matching the request's endpoint against the endpoints of the
    views registered within each Admin instance.

    If called from outside an Admin view (e.g., a public homepage), it
    falls back to the theme of the first registered Admin instance.

    :return:
        The theme folder (e.g., 'bootstrap5').
        Returns 'bootstrap4' as a safe fallback.
    """
    fallback_folder = "bootstrap4"

    try:
        # 1. Get the list of all registered Admin instances.
        admins = current_app.extensions.get("admin", [])
        if not admins:
            return fallback_folder

        # 2. Determine the correct Admin instance by checking its views.
        target_admin = None
        current_endpoint = getattr(request, "endpoint", None)

        if current_endpoint:
            # A flag to break out of the outer loop once a match is found.
            found_admin = False
            for admin in admins:
                # We loop through each view registered in this Admin instance.
                for view in admin._views:
                    # Check if the current endpoint belongs to this view.
                    if current_endpoint.startswith(view.endpoint):
                        target_admin = admin
                        found_admin = True
                        break  # Found the correct view. Exit inner loop.
                if found_admin:
                    break  # Exit outer loop.

        # If no matching view was found (e.g., on a public page) or if we are
        # outside a request, fall back to the first registered admin.
        if target_admin is None:
            target_admin = admins[0]

        # 3. Extract the theme folder from the chosen instance.
        theme_obj = getattr(target_admin, "theme", None)
        if theme_obj:
            folder = getattr(theme_obj, "folder", None)
            if folder:
                return folder

    except (RuntimeError, IndexError):
        # RuntimeError: Called outside an active Flask app/request context.
        # IndexError: `admins` list was somehow empty after the initial check.
        pass

    # Return the ultimate fallback folder if any step above failed.
    return fallback_folder
