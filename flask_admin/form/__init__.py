from wtforms import form
from wtforms.fields.core import UnboundField

from .fields import *
from .widgets import *
from .upload import *


class BaseForm(form.Form):
    def __init__(self, formdata=None, obj=None, prefix=u'', **kwargs):
        self._obj = obj

        super(BaseForm, self).__init__(formdata=formdata, obj=obj, prefix=prefix, **kwargs)


class FormOpts(object):
    __slots__ = ['widget_args', 'form_rules']

    def __init__(self, widget_args=None, form_rules=None):
        self.widget_args = widget_args or {}
        self.form_rules = form_rules


def recreate_field(unbound):
    """
        Create new instance of the unbound field, resetting wtforms creation counter.

        :param unbound:
            UnboundField instance
    """
    if not isinstance(unbound, UnboundField):
        raise ValueError('recreate_field expects UnboundField instance, %s was passed.' % type(unbound))

    return unbound.field_class(*unbound.args, **unbound.kwargs)
