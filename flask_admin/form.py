import time
import datetime

from flask.globals import _request_ctx_stack

from flask.ext import wtf
from wtforms import fields, widgets

from flask.ext.admin.babel import gettext, ngettext


class BaseForm(wtf.Form):
    """
        Customized form class.
    """
    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        if formdata:
            super(BaseForm, self).__init__(formdata, obj, prefix, **kwargs)
        else:
            super(BaseForm, self).__init__(obj=obj, prefix=prefix, **kwargs)

        self._obj = obj

    @property
    def has_file_field(self):
        """
            Return True if form contains at least one FileField.
        """
        # TODO: Optimize me
        for f in self:
            if isinstance(f, wtf.FileField):
                return True

        return False


class TimeField(fields.Field):
    """
        A text field which stores a `datetime.time` object.
        Accepts time string in multiple formats: 20:10, 20:10:00, 10:00 am, 9:30pm, etc.
    """
    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None, formats=None, **kwargs):
        """
            Constructor

            :param label:
                Label
            :param validators:
                Field validators
            :param formats:
                Supported time formats, as a enumerable.
            :param kwargs:
                Any additional parameters
        """
        super(TimeField, self).__init__(label, validators, **kwargs)

        self.format = formats or ('%H:%M:%S', '%H:%M',
                                  '%I:%M:%S%p', '%I:%M%p',
                                  '%I:%M:%S %p', '%I:%M %p')

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)

            for format in self.formats:
                try:
                    timetuple = time.strptime(date_str, format)
                    self.data = datetime.time(timetuple.tm_hour,
                                              timetuple.tm_min,
                                              timetuple.tm_sec)
                    return
                except ValueError:
                    pass

            raise ValueError(gettext('Invalid time format'))


class Select2Widget(widgets.Select):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form.js and select2 stylesheet for it to
        work.
    """
    def __call__(self, field, **kwargs):
        allow_blank = getattr(field, 'allow_blank', False)

        if allow_blank and not self.multiple:
            kwargs['data-role'] = u'select2blank'
        else:
            kwargs['data-role'] = u'select2'

        return super(Select2Widget, self).__call__(field, **kwargs)


class Select2Field(fields.SelectField):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form.js and select2 stylesheet for it to
        work.
    """
    widget = Select2Widget()


class DatePickerWidget(widgets.TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datepicker'
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(widgets.TextInput):
    """
        Datetime picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datetimepicker'
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class RenderTemplateWidget(object):
    """
        WTForms widget that renders Jinja2 template
    """
    def __init__(self, template):
        """
            Constructor

            :param template:
                Template path
        """
        self.template = template

    def __call__(self, field, **kwargs):
        ctx = _request_ctx_stack.top
        jinja_env = ctx.app.jinja_env

        kwargs.update({
            'field': field,
            '_gettext': gettext,
            '_ngettext': ngettext})

        template = jinja_env.get_template(self.template)
        return template.render(kwargs)


class Select2TagsWidget(widgets.TextInput):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text widget.
    You must include select2.js, form.js and select2 stylesheet for it to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'select2tags'
        return super(Select2TagsWidget, self).__call__(field, **kwargs)


class Select2TagsField(fields.TextField):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text field.
    You must include select2.js, form.js and select2 stylesheet for it to work.
    """
    widget = Select2TagsWidget()

    def __init__(self, label=None, validators=None, save_as_list=False, **kwargs):
        """Initialization

        :param save_as_list:
            If `True` then populate ``obj`` using list else string
        """
        self.save_as_list = save_as_list
        super(Select2TagsField, self).__init__(label, validators, **kwargs)

    def process_formdata(self, valuelist):
        if self.save_as_list:
            self.data = [v.strip() for v in valuelist[0].split(',') if v.strip()]
        else:
            self.data = valuelist[0]

    def _value(self):
        return u', '.join(self.data) if isinstance(self.data, list) else self.data
