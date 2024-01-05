import time
import datetime
import json
import re

from wtforms import fields
from flask_admin.babel import gettext
from flask_admin._compat import text_type, as_unicode

from . import widgets as admin_widgets

"""
An understanding of WTForms's Custom Widgets is helpful for understanding this code:
http://wtforms.simplecodes.com/docs/0.6.2/widgets.html#custom-widgets
"""

__all__ = ['DateTimeField', 'TimeField', 'Select2Field', 'Select2TagsField',
           'JSONField']


class DateTimeField(fields.DateTimeField):
    """
       Allows modifying the datetime format of a DateTimeField using form_args.
    """
    widget = admin_widgets.DateTimePickerWidget()

    def __init__(self, label=None, validators=None, format=None, **kwargs):
        """
            Constructor

            :param label:
                Label
            :param validators:
                Field validators
            :param format:
                Format for text to date conversion. Defaults to '%Y-%m-%d %H:%M:%S'
            :param kwargs:
                Any additional parameters
        """
        super(DateTimeField, self).__init__(
            label, validators, format or '%Y-%m-%d %H:%M:%S', **kwargs)


class TimeField(fields.Field):
    """
        A text field which stores a `datetime.time` object.
        Accepts time string in multiple formats: 20:10, 20:10:00, 10:00 am, 9:30pm, etc.
    """
    widget = admin_widgets.TimePickerWidget()

    def __init__(self, label=None, validators=None, formats=None,
                 default_format=None, widget_format=None, **kwargs):
        """
            Constructor

            :param label:
                Label
            :param validators:
                Field validators
            :param formats:
                Supported time formats, as a enumerable.
            :param default_format:
                Default time format. Defaults to '%H:%M:%S'
            :param kwargs:
                Any additional parameters
        """
        super(TimeField, self).__init__(label, validators, **kwargs)

        self.formats = formats or ('%H:%M:%S', '%H:%M',
                                   '%I:%M:%S%p', '%I:%M%p',
                                   '%I:%M:%S %p', '%I:%M %p')

        self.default_format = default_format or '%H:%M:%S'

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        elif self.data is not None:
            return self.data.strftime(self.default_format)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)

            if date_str.strip():
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
            else:
                self.data = None


class Select2Field(fields.SelectField):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form-x.x.x.js and select2 stylesheet for it to
        work.
    """
    widget = admin_widgets.Select2Widget()

    def __init__(self, label=None, validators=None, coerce=text_type,
                 choices=None, allow_blank=False, blank_text=None, **kwargs):
        super(Select2Field, self).__init__(
            label, validators, coerce, choices, **kwargs
        )
        self.allow_blank = allow_blank
        self.blank_text = blank_text or ' '

    def iter_choices(self):
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)

        for choice in self.choices:
            if isinstance(choice, tuple):
                yield (choice[0], choice[1], self.coerce(choice[0]) == self.data)
            else:
                yield (choice.value, choice.name, self.coerce(choice.value) == self.data)

    def process_data(self, value):
        if value is None:
            self.data = None
        else:
            try:
                self.data = self.coerce(value)
            except (ValueError, TypeError):
                self.data = None

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == '__None':
                self.data = None
            else:
                try:
                    self.data = self.coerce(valuelist[0])
                except ValueError:
                    raise ValueError(self.gettext(u'Invalid Choice: could not coerce'))

    def pre_validate(self, form):
        if self.allow_blank and self.data is None:
            return

        super(Select2Field, self).pre_validate(form)


class Select2TagsField(fields.StringField):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text field.
    You must include select2.js, form-x.x.x.js and select2 stylesheet for it to work.
    """
    widget = admin_widgets.Select2TagsWidget()
    _strip_regex = re.compile(r'#\d+(?:(,)|\s$)')  # e.g., 'tag#123, anothertag#425 ' => 'tag, anothertag'

    def __init__(self, label=None, validators=None, save_as_list=False, coerce=text_type, allow_duplicates=False,
                 **kwargs):
        """Initialization

        :param save_as_list:
            If `True` then populate ``obj`` using list else string
        :param allow_duplicates
            If `True` then duplicate tags are allowed in the field.
        """
        self.save_as_list = save_as_list
        self.allow_duplicates = allow_duplicates
        self.coerce = coerce

        super(Select2TagsField, self).__init__(label, validators, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            entrylist = valuelist[0]
            if self.allow_duplicates and entrylist.endswith(' '):
                # This means this is an allowed duplicate (see form.js, `createSearchChoice`), so its ID was modified.
                # Hence, we need to restore the original IDs.
                entrylist = re.sub(self._strip_regex, '\\1', entrylist)
            if self.save_as_list:
                self.data = [self.coerce(v.strip()) for v in entrylist.split(',') if v.strip()]
            else:
                self.data = self.coerce(entrylist)

    def _value(self):
        if isinstance(self.data, (list, tuple)):
            return u','.join(as_unicode(v) for v in self.data)
        elif self.data:
            return as_unicode(self.data)
        else:
            return u''


class JSONField(fields.TextAreaField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            # prevent utf8 characters from being converted to ascii
            return as_unicode(json.dumps(self.data, ensure_ascii=False))
        else:
            return '{}'

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]

            # allow saving blank field as None
            if not value:
                self.data = None
                return

            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext('Invalid JSON'))
