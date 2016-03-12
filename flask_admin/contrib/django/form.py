from wtforms import fields as f, validators

from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin.model.form import FieldPlaceholder
from flask_admin.model.form import ModelConverterBase


def converts(*args):
    def _inner(func):
        func._converter_for = frozenset(args)
        return func
    return _inner


class CustomModelConverter(ModelConverterBase):

    def __init__(self, view):
        super(CustomModelConverter, self).__init__()

        self.view = view

    def convert(self, model, field, field_args):
        from django.db.models.fields import NOT_PROVIDED
        kwargs = {
            'label': getattr(field, 'verbose_name', field.name).decode('utf-8'),
            'description': field.help_text or '',
            'validators': [],
            'filters': [],
#             'default': field.default,
        }
        if field.default != NOT_PROVIDED:
            kwargs['default'] = field.default

        if field_args:
            kwargs.update(field_args)

        if field.null:
            kwargs['validators'].append(validators.Required())
        else:
            kwargs['validators'].append(validators.Optional())

        ftype = type(field).__name__

        if field.choices:
            kwargs['choices'] = field.choices

            if ftype in self.converters:
                kwargs["coerce"] = self.coerce(ftype)
            if kwargs.pop('multiple', False):
                return f.SelectMultipleField(**kwargs)
            return f.SelectField(**kwargs)

        ftype = type(field).__name__

        if hasattr(field, 'to_form_field'):
            return field.to_form_field(model, kwargs)

        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)

    @classmethod
    def _string_common(cls, model, field, kwargs):
        if field.max_length or field.min_length:
            kwargs['validators'].append(
                validators.Length(max=field.max_length or - 1,
                                  min=- 1))

    @converts('CharField')
    def conv_String(self, model, field, kwargs):
        if 'password' in kwargs:
            if kwargs.pop('password'):
                return f.PasswordField(**kwargs)
        if field.max_length:
            return f.StringField(**kwargs)
        return f.TextAreaField(**kwargs)

    @converts('URLField')
    def conv_URL(self, model, field, kwargs):
        kwargs['validators'].append(validators.URL())
        self._string_common(model, field, kwargs)
        return f.StringField(**kwargs)

    @converts('EmailField')
    def conv_Email(self, model, field, kwargs):
        kwargs['validators'].append(validators.Email())
        self._string_common(model, field, kwargs)
        return f.StringField(**kwargs)

    @converts('IntegerField')
    def conv_Int(self, model, field, kwargs):
        #self._number_common(model, field, kwargs)
        return f.IntegerField(**kwargs)

    @converts('FloatField')
    def conv_Float(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.FloatField(**kwargs)

    @converts('DecimalField')
    def conv_Decimal(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.DecimalField(**kwargs)

    @converts('BooleanField')
    def conv_Boolean(self, model, field, kwargs):
        return f.BooleanField(**kwargs)

    @converts('DateTimeField')
    def conv_DateTime(self, model, field, kwargs):
        kwargs['widget'] = form.DateTimePickerWidget()
        return f.DateTimeField(**kwargs)


def get_form(model, converter,
             base_class=form.BaseForm,
             only=None,
             exclude=None,
             field_args=None,
             extra_fields=None):

    field_args = field_args or {}

    # Find properties
    properties = sorted(((v.name, v) for v in model._meta.fields))

    if only:
        props = dict(properties)

        def find(name):
            if extra_fields and name in extra_fields:
                return FieldPlaceholder(extra_fields[name])

            p = props.get(name)
            if p is not None:
                return p

            raise ValueError('Invalid model property name %s.%s' % (model, name))

        properties = ((p, find(p)) for p in only)
    elif exclude:
        properties = (p for p in properties if p[0] not in exclude)

    # Create fields
    field_dict = {}
    for name, p in properties:
        field = converter.convert(model, p, field_args.get(name))
        if field is not None:
            field_dict[name] = field

    # Contribute extra fields
    if not only and extra_fields:
        for name, field in iteritems(extra_fields):
            field_dict[name] = form.recreate_field(field)

    field_dict['model_class'] = model
    return type(model.__name__ + 'Form', (base_class,), field_dict)
