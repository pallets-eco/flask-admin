from flask import url_for, json
from wtforms.widgets import HTMLString, html_params

from flask.ext.admin.form import RenderTemplateWidget


class InlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFieldListWidget, self).__init__('admin/model/inline_field_list.html')


class InlineFormWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormWidget, self).__init__('admin/model/inline_form.html')


class AjaxSelect2Widget(object):
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'select2-ajax'
        kwargs['data-url'] = url_for('.ajax_lookup', name=field.loader.name)

        allow_blank = getattr(field, 'allow_blank', False)
        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'hidden')

        if self.multiple:
            result = []

            for value in field.data:
                result.append(field.loader.format(value))

            kwargs['value'] = json.dumps(result)
            kwargs['data-multiple'] = u'1'
        else:
            kwargs['value'] = json.dumps(field.loader.format(field.data))

        return HTMLString('<input %s>' % html_params(name=field.name, **kwargs))
