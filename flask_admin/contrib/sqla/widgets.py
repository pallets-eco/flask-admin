from markupsafe import Markup
from wtforms.widgets.core import escape  # type: ignore[attr-defined]


class CheckboxListInput:
    """
    Alternative widget for many-to-many relationships.

    Appears as the list of checkboxes.
    """

    template = (
        '<div class="checkbox">'
        " <label>"
        '  <input id="%(id)s" name="%(name)s" value="%(id)s" '
        'type="checkbox"%(selected)s>%(label)s'
        " </label>"
        "</div>"
    )

    def __call__(self, field, **kwargs):
        items = []
        for field_choices in field.iter_choices():
            if len(field_choices) == 3:  # wtforms <3.1, >=3.1.1, <3.2
                value, label, selected = field_choices
            else:
                value, label, selected, _ = field_choices
            args = {
                "id": value,
                "name": field.name,
                "label": escape(label),
                "selected": " checked" if selected else "",
            }
            items.append(self.template % args)
        return Markup("".join(items))
