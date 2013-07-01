from mongoengine import ReferenceField

from wtforms import fields, validators
from flask.ext.mongoengine.wtf import orm, fields as mongo_fields

from flask.ext.admin import form
from flask.ext.admin.model.fields import InlineFieldList
from flask.ext.admin.model.widgets import InlineFormWidget

from .fields import ModelFormField


class CustomModelConverter(orm.ModelConverter):
    """
        Customized MongoEngine form conversion class.

        Injects various Flask-Admin widgets and handles lists with
        customized InlineFieldList field.
    """

    def __init__(self, view):
        super(CustomModelConverter, self).__init__()

        self.view = view

    def _get_field_override(self, name):
        form_overrides = getattr(self.view, 'form_overrides', None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def convert(self, model, field, field_args):
        kwargs = {
            'label': getattr(field, 'verbose_name', field.name),
            'description': field.help_text or '',
            'validators': [],
            'filters': [],
            'default': field.default,
        }

        if field_args:
            kwargs.update(field_args)

        if field.required:
            kwargs['validators'].append(validators.Required())
        else:
            kwargs['validators'].append(validators.Optional())

        ftype = type(field).__name__

        if field.choices:
            kwargs['choices'] = field.choices

            if ftype in self.converters:
                kwargs["coerce"] = self.coerce(ftype)
            if kwargs.pop('multiple', False):
                return fields.SelectMultipleField(**kwargs)
            return fields.SelectField(**kwargs)

        ftype = type(field).__name__

        if hasattr(field, 'to_form_field'):
            return field.to_form_field(model, kwargs)

        override = self._get_field_override(field.name)
        if override:
            return override(**kwargs)

        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)

    @orm.converts('DateTimeField')
    def conv_DateTime(self, model, field, kwargs):
        kwargs['widget'] = form.DateTimePickerWidget()
        return orm.ModelConverter.conv_DateTime(self, model, field, kwargs)

    @orm.converts('ListField')
    def conv_List(self, model, field, kwargs):
        if isinstance(field.field, ReferenceField):
            kwargs['widget'] = form.Select2Widget(multiple=True)

            doc_type = field.field.document_type
            return mongo_fields.ModelSelectMultipleField(model=doc_type, **kwargs)
        if field.field.choices:
            kwargs['multiple'] = True
            return self.convert(model, field.field, kwargs)

        unbound_field = self.convert(model, field.field, {})
        kwargs = {
            'validators': [],
            'filters': [],
        }
        return InlineFieldList(unbound_field, min_entries=0, **kwargs)

    @orm.converts('EmbeddedDocumentField')
    def conv_EmbeddedDocument(self, model, field, kwargs):
        kwargs = {
            'validators': [],
            'filters': [],
            'widget': InlineFormWidget()
        }

        form_class = model_form(field.document_type_obj, field_args={})
        return ModelFormField(field.document_type_obj, form_class, **kwargs)

    @orm.converts('ReferenceField')
    def conv_Reference(self, model, field, kwargs):
        kwargs['widget'] = form.Select2Widget()
        return orm.ModelConverter.conv_Reference(self, model, field, kwargs)


def model_form(model, base_class=form.BaseForm, only=None, exclude=None,
               field_args=None, converter=None):
    return orm.model_form(model, base_class=base_class, only=only,
                          exclude=exclude, field_args=field_args,
                          converter=converter)
