from flask import json
from wtforms.widgets import HTMLString, html_params

from flask.ext.admin._compat import as_unicode
from flask.ext.admin.babel import gettext
from flask.ext.admin.helpers import get_url
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
        kwargs.setdefault('data-role', 'select2-ajax')
        kwargs.setdefault('data-url', get_url('.ajax_lookup', name=field.loader.name))

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


class XEditableWidget(object):
    """
        WTForms widget that provides in-line editing for the list view.

        Determines how to display the x-editable/ajax form based on the
        field inside of the FieldList (StringField, IntegerField, etc).
    """
    def __call__(self, field, **kwargs):
        value = kwargs.pop("value", "")

        kwargs.setdefault('data-role', 'x-editable')
        kwargs.setdefault('data-url', './ajax/update/')

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)
        kwargs.setdefault('href', '#')

        if not kwargs.get('pk'):
            raise Exception('pk required')
        kwargs['data-pk'] = str(kwargs.pop("pk"))

        kwargs['data-csrf'] = kwargs.pop("csrf", "")

        # gets the first entry (subfield) from FieldList (field) and uses the
        # subfield.type (`kwargs_` method) to determine kwargs
        subfield = field.entries[0]
        try:
            kwargs = getattr(self, 'kwargs_' + subfield.type)(subfield, kwargs)
        except AttributeError:
            raise Exception('Unsupported field type: %s' % (type(subfield),))

        return HTMLString(
            '<a %s>%s</a>' % (html_params(**kwargs), value)
        )

    """
        `kwargs_` methods are used to allow overriding XEditableWidget and
        adding new kwargs_ methods for custom fields (without much code)
    """
    def kwargs_StringField(self, subfield, kwargs):
        kwargs['data-type'] = 'text'
        return kwargs

    def kwargs_TextAreaField(self, subfield, kwargs):
        kwargs['data-type'] = 'textarea'
        kwargs['data-rows'] = '5'
        return kwargs

    def kwargs_BooleanField(self, subfield, kwargs):
        kwargs['data-type'] = 'select'
        # data-source = dropdown options
        kwargs['data-source'] = {'': 'False', '1': 'True'}
        kwargs['data-role'] = 'x-editable-boolean'
        return kwargs

    def kwargs_Select2Field(self, subfield, kwargs):
        kwargs['data-type'] = 'select'
        kwargs['data-source'] = dict(subfield.choices)
        return kwargs

    def kwargs_DateField(self, subfield, kwargs):
        kwargs['data-type'] = 'combodate'
        kwargs['data-format'] = 'YYYY-MM-DD'
        kwargs['data-template'] = 'YYYY-MM-DD'
        return kwargs

    def kwargs_DateTimeField(self, subfield, kwargs):
        kwargs['data-type'] = 'combodate'
        kwargs['data-format'] = 'YYYY-MM-DD HH:mm:ss'
        kwargs['data-template'] = 'YYYY-MM-DD  HH:mm:ss'
        # x-editable-combodate uses 1 minute increments
        kwargs['data-role'] = 'x-editable-combodate'
        return kwargs

    def kwargs_TimeField(self, subfield, kwargs):
        kwargs['data-type'] = 'combodate'
        kwargs['data-format'] = 'HH:mm:ss'
        kwargs['data-template'] = 'HH:mm:ss'
        kwargs['data-role'] = 'x-editable-combodate'
        return kwargs

    def kwargs_IntegerField(self, subfield, kwargs):
        kwargs['data-type'] = 'number'
        return kwargs

    def kwargs_FloatField(self, subfield, kwargs):
        kwargs['data-type'] = 'number'
        kwargs['data-step'] = 'any'
        return kwargs

    def kwargs_DecimalField(self, subfield, kwargs):
        return self.kwargs_FloatField(subfield, kwargs)

    def kwargs_QuerySelectField(self, subfield, kwargs):
        kwargs['data-type'] = 'select'
        
        choices = {}
        for choice in subfield:
            try:
                choices[str(choice._value())] = str(choice.label.text)
            except TypeError:
                choices[str(choice._value())] = ""
        kwargs['data-source'] = choices
        return kwargs

    def kwargs_ModelSelectField(self, subfield, kwargs):
        return self.kwargs_QuerySelectField(subfield, kwargs)
