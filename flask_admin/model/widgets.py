import typing as t

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
            ids = []

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
    WTForms widget that provides HTMX-powered in-line editing for the list view.

    Renders a clickable <span> with hx-get to fetch the edit form on click.
    The edit form is returned as an HTML fragment by the ajax_edit endpoint.
    """

    def __call__(self, field: Field, **kwargs: t.Any) -> str:
        display_value = kwargs.pop("display_value", "")

        if not kwargs.get("pk"):
            raise Exception("pk required")
        pk = str(kwargs.pop("pk"))

        kwargs.pop("csrf", "")  # not needed in display state

        field_name = field.name
        target_id = f"editable-{field_name}-{pk}"

        return Markup(
            f'<span hx-get="./ajax/edit/?pk={escape(pk)}&amp;field={escape(field_name)}"'
            f' hx-target="#{target_id}"'
            f' hx-swap="innerHTML"'
            f""" hx-on::before-request="this.closest('td').dataset.original = this.closest('td').innerHTML" """
            f' class="editable-cell"'
            f' title="Click to edit">'
            f"{escape(display_value)}"
            f"</span>"
        )


# Backwards compatibility alias
XEditableWidget = HTMXEditableWidget
