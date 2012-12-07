import inspect

from flask.ext.admin.form import BaseForm


def converts(*args):
    def _inner(func):
        func._converter_for = frozenset(args)
        return func
    return _inner


class InlineFormAdmin(object):
    """
        Settings for inline form administration.

        You can use this class to customize displayed form.
        For example::

            class MyUserInfoForm(InlineFormAdmin):
                form_columns = ('name', 'email')
    """
    _defaults = ['form_columns', 'form_excluded_columns', 'form_args']

    def __init__(self, model, **kwargs):
        """
            Constructor

            :param model:
                Target model class
            :param kwargs:
                Additional options
        """
        self.model = model

        for k in self._defaults:
            if not hasattr(self, k):
                setattr(self, k, None)

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def postprocess_form(self, form_class):
        """
            Post process form. Use this to contribute fields.

            For example::

                class MyInlineForm(InlineFormAdmin):
                    def postprocess_form(self, form):
                        form.value = wtf.TextField('value')
                        return form

                class MyAdmin(ModelView):
                    inline_models = (MyInlineForm(ValueModel),)
        """
        return form_class


class ModelConverterBase(object):
    def __init__(self, converters=None, use_mro=True):
        self.use_mro = use_mro

        if not converters:
            converters = {}

        for name in dir(self):
            obj = getattr(self, name)
            if hasattr(obj, '_converter_for'):
                for classname in obj._converter_for:
                    converters[classname] = obj

        self.converters = converters

    def get_converter(self, column):
        if self.use_mro:
            types = inspect.getmro(type(column.type))
        else:
            types = [type(column.type)]

        # Search by module + name
        for col_type in types:
            type_string = '%s.%s' % (col_type.__module__, col_type.__name__)

            if type_string in self.converters:
                return self.converters[type_string]

        # Search by name
        for col_type in types:
            if col_type.__name__ in self.converters:
                return self.converters[col_type.__name__]

        return None

    def get_form(self, model, base_class=BaseForm,
                only=None, exclude=None,
                field_args=None):
        raise NotImplemented()


class InlineModelConverterBase(object):
    def __init__(self, view):
        """
            Base constructor

            :param view:
                View class
        """
        self.view = view

    def get_label(self, info, name):
        """
            Get inline model field label

            :param info:
                Inline model info
            :param name:
                Field name
        """
        form_name = getattr(info, 'form_label', None)
        if form_name:
            return form_name

        column_labels = getattr(self.view, 'column_labels', None)

        if column_labels and name in column_labels:
            return column_labels[name]

        return None

    def get_info(self, p):
        """
            Figure out InlineFormAdmin information.

            :param p:
                Inline model. Can be one of:

                 - ``tuple``, first value is related model instance,
                 second is dictionary with options
                 - ``InlineFormAdmin`` instance
                 - Model class
        """
        if isinstance(p, tuple):
            return InlineFormAdmin(p[0], **p[1])
        elif isinstance(p, InlineFormAdmin):
            return p

        return None
