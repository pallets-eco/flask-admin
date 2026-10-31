import typing as t
import warnings
from urllib.parse import quote

from flask import json
from markupsafe import escape
from markupsafe import Markup
from wtforms import Field
from wtforms.widgets import html_params

from flask_admin._compat import as_unicode
from flask_admin._types import T_AJAX_SELECT_FIELD
from flask_admin.babel import gettext
from flask_admin.form import RenderTemplateWidget
from flask_admin.helpers import get_url


class InlineFieldListWidget(RenderTemplateWidget):
    def __init__(self) -> None:
        super().__init__("admin/model/inline_field_list.html")


class InlineFormWidget(RenderTemplateWidget):
    def __init__(self) -> None:
        super().__init__("admin/model/inline_form.html")

    def __call__(self, field: Field, **kwargs: t.Any) -> str:
        kwargs.setdefault("form_opts", getattr(field, "form_opts", None))
        return super().__call__(field, **kwargs)


class AjaxSelect2Widget:
    def __init__(self, multiple: bool = False) -> None:
        self.multiple = multiple

    def __call__(self, field: T_AJAX_SELECT_FIELD, **kwargs: t.Any) -> str:
        kwargs.setdefault("data-role", "select2-ajax")
        kwargs.setdefault("data-url", get_url(".ajax_lookup", name=field.loader.name))

        allow_blank = getattr(field, "allow_blank", False)
        if allow_blank and not self.multiple:
            kwargs["data-allow-blank"] = "1"

        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", "hidden")

        if self.multiple:
            result = []
            ids: list[str] = []

            for value in field.data:
                data = field.loader.format(value)
                result.append(data)
                ids.append(as_unicode(data[0]))  # type: ignore[index]

            separator = getattr(field, "separator", ",")

            kwargs["value"] = separator.join(ids)
            kwargs["data-json"] = json.dumps(result)
            kwargs["data-multiple"] = "1"
            kwargs["data-separator"] = separator
        else:
            data = field.loader.format(field.data)

            if data:
                kwargs["value"] = data[0]
                kwargs["data-json"] = json.dumps(data)

        placeholder = field.loader.options.get(
            "placeholder", gettext("Please select model")
        )
        kwargs.setdefault("data-placeholder", placeholder)

        minimum_input_length = int(field.loader.options.get("minimum_input_length", 1))
        kwargs.setdefault("data-minimum-input-length", minimum_input_length)

        kwargs.setdefault("data-separator", ",")

        return Markup(f"<input {html_params(name=field.name, **kwargs)}>")


class HTMXEditableWidget:
    """
    WTForms widget providing HTMX-powered inline editing for the list view.

    Renders a clickable element that swaps itself, via HTMX, for an edit
    form fetched from the ``ajax_edit`` endpoint; submitting that form posts
    back to ``ajax_update``.

    This replaces the previous implementation (``XEditableWidget``), which
    rendered ``data-*`` attributes for the now-unmaintained x-editable
    jQuery plugin to interpret client-side. ``XEditableWidget`` remains
    importable as a deprecated alias of this class -- see the module-level
    docstring below for the migration path if you subclassed it.
    """

    def __call__(self, field: Field, **kwargs: t.Any) -> str:
        pk = kwargs.pop("pk", None)
        if pk is None:
            raise ValueError("HTMXEditableWidget requires 'pk'")

        # Accepted (and ignored) so that call sites and XEditableWidget
        # subclasses that used to pass a csrf kwarg keep working unchanged.
        # The CSRF token now travels inside the fetched edit-form fragment
        # (rendered by ajax_edit) instead of living on the display element.
        kwargs.pop("csrf", None)

        display_value = escape(kwargs.get("display_value", ""))
        field_name = escape(field.name)
        pk_str = str(pk)

        # Percent-encode for the querystring (so pks containing '&', '#',
        # '%', etc. can't corrupt it or the pk/field split), and separately
        # HTML-escape for use inside the id/CSS-selector attributes.
        pk_url = quote(pk_str, safe="")
        pk_html = escape(pk_str)

        return Markup(
            f'<span id="editable-{field_name}-{pk_html}"'
            f' hx-get="./ajax/edit/?pk={pk_url}&field={field_name}"'
            f' hx-target="this"'
            f' hx-swap="beforeend"'
            f' class="editable-cell"'
            f' title="{escape(gettext("Click to edit"))}"'
            f">{display_value}</span>"
        )

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        if "get_kwargs" in cls.__dict__:
            warnings.warn(
                f"{cls.__name__} overrides get_kwargs(), which is no longer "
                "called. get_kwargs() customized XEditableWidget's "
                "attribute-driven rendering for the x-editable jQuery "
                "plugin; HTMXEditableWidget renders server-side instead, so "
                "there is no equivalent target for its return value. "
                "Override __call__() instead, e.g.:\n\n"
                "    class CustomWidget(HTMXEditableWidget):\n"
                "        def __call__(self, field, **kwargs):\n"
                "            # custom rendering logic\n"
                "            return super().__call__(field, **kwargs)\n",
                DeprecationWarning,
                stacklevel=2,
            )


# Backwards-compatible alias. XEditableWidget rendered inline editing by
# emitting data-* attributes for the (now unmaintained) x-editable jQuery
# plugin to interpret; that implementation has been removed and replaced
# with HTMXEditableWidget above. The name is kept -- as a plain alias to the
# *same* class, not a subclass -- so that:
#   * `from flask_admin.model.widgets import XEditableWidget` keeps working,
#     including under static type checkers (this is a real assignment, not
#     dynamically synthesized), and
#   * `isinstance(widget, XEditableWidget)` / `issubclass(..., XEditableWidget)`
#     behave identically whether a widget was constructed via
#     `XEditableWidget()` or `HTMXEditableWidget()`, since they're the same
#     object.
# Constructing it now renders the HTMX-based markup. If you subclassed it to
# override get_kwargs(), that method is no longer called; see the
# DeprecationWarning raised by __init_subclass__ above for the migration
# path (override __call__ instead).
XEditableWidget = HTMXEditableWidget
