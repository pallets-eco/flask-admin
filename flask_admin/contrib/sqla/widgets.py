from wtforms.widgets.core import escape

from flask_admin._backwards import Markup


class CheckboxListInput:
    """
    Alternative widget for many-to-many relationships.

    Appears as the list of checkboxes.
    """
    template = (
        '<div class="checkbox">'
        ' <label>'
        '  <input id="%(id)s" name="%(name)s" value="%(id)s" '
        'type="checkbox"%(selected)s>%(label)s'
        ' </label>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        items = []
        for val, label, selected in field.iter_choices():
            args = {
                'id': val,
                'name': field.name,
                'label': escape(label),
                'selected': ' checked' if selected else '',
            }
            items.append(self.template % args)
        return Markup(''.join(items))
