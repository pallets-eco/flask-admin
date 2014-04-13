from flask import url_for, json
from wtforms.widgets import HTMLString, html_params

from flask.ext.admin._compat import as_unicode
from flask.ext.admin.babel import gettext
from flask.ext.admin.form import RenderTemplateWidget


class InlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFieldListWidget, self).__init__('admin/model/inline_field_list.html')


class InlineFormWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormWidget, self).__init__('admin/model/inline_form.html')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('form_opts', getattr(field, 'form_opts', None))
        return super(InlineFormWidget, self).__call__(field, **kwargs)


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
            ids = []

            for value in field.data:
                data = field.loader.format(value)
                result.append(data)
                ids.append(as_unicode(data[0]))

            separator = getattr(field, 'separator', ',')

            kwargs['value'] = separator.join(ids)
            kwargs['data-json'] = json.dumps(result)
            kwargs['data-multiple'] = u'1'
        else:
            data = field.loader.format(field.data)

            if data:
                kwargs['value'] = data[0]
                kwargs['data-json'] = json.dumps(data)

        placeholder = gettext(field.loader.options.get('placeholder', 'Please select model'))
        kwargs.setdefault('data-placeholder', placeholder)

        return HTMLString('<input %s>' % html_params(name=field.name, **kwargs))
