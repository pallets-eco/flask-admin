from wtforms import fields

from peewee import DateTimeField, DateField, TimeField, BaseModel, ForeignKeyField

from wtfpeewee.orm import ModelConverter, model_form

from flask.ext.admin import form
from flask.ext.admin.model.form import InlineFormAdmin
from flask.ext.admin.model.fields import InlineModelFormField
from flask.ext.admin.model.widgets import InlineFormListWidget

from .tools import get_primary_key


class InlineModelFormList(fields.FieldList):
    widget = InlineFormListWidget()

    def __init__(self, form, model, prop, **kwargs):
        self.form = form
        self.model = model
        self.prop = prop

        self._pk = get_primary_key(model)

        super(InlineModelFormList, self).__init__(InlineModelFormField(form, self._pk), **kwargs)

    def __call__(self, **kwargs):
        return self.widget(self, template=self.form(), **kwargs)

    def process(self, formdata, data=None):
        if not formdata:
            data = self.model.select().where(user=data).execute()
        else:
            data = None

        return super(InlineModelFormList, self).process(formdata, data)

    def populate_obj(self, obj, name):
        pass

    def save_related(self, obj):
        model_id = getattr(obj, self._pk)

        values = self.model.select().where(user=model_id).execute()

        pk_map = dict((str(getattr(v, self._pk)), v) for v in values)

        # Handle request data
        for field in self.entries:
            field_id = field.get_pk()

            if field_id in pk_map:
                model = pk_map[field_id]

                if field.should_delete():
                    model.delete_instance(recursive=True)
                    continue
            else:
                model = self.model()

            field.populate_obj(model, None)

            # Force relation
            setattr(model, self.prop, model_id)

            model.save()


class CustomModelConverter(ModelConverter):
    def __init__(self, additional=None):
        super(CustomModelConverter, self).__init__(additional)
        self.converters[DateTimeField] = self.handle_datetime
        self.converters[DateField] = self.handle_date
        self.converters[TimeField] = self.handle_time

    def handle_date(self, model, field, **kwargs):
        kwargs['widget'] = form.DatePickerWidget()
        return field.name, fields.DateField(**kwargs)

    def handle_datetime(self, model, field, **kwargs):
        kwargs['widget'] = form.DateTimePickerWidget()
        return field.name, fields.DateTimeField(**kwargs)

    def handle_time(self, model, field, **kwargs):
        return field.name, form.TimeField(**kwargs)


def contribute_inline(model, form_class, inline_models):
    # Contribute columns
    for p in inline_models:
        # Figure out settings
        if isinstance(p, tuple):
            info = InlineFormAdmin(p[0], **p[1])
        elif isinstance(p, InlineFormAdmin):
            info = p
        elif isinstance(p, BaseModel):
            info = InlineFormAdmin(p)
        else:
            model = getattr(p, 'model', None)

            if model is None:
                raise Exception('Unknown inline model admin: %s' % repr(p))

            attrs = dict()
            for attr in dir(p):
                if not attr.startswith('_') and attr != model:
                    attrs[attr] = getattr(p, attr)

            info = InlineFormAdmin(model, **attrs)

        # Find property from target model to current model
        reverse_field = None

        for field in info.model._meta.get_fields():
            field_type = type(field)

            if field_type == ForeignKeyField:
                if field.to == model:
                    reverse_field = field
                    break
        else:
            raise Exception('Cannot find reverse relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_field.name]

        if info.excluded_form_columns:
            exclude = ignore + info.excluded_form_columns
        else:
            exclude = ignore

        # Create field
        converter = CustomModelConverter()
        child_form = model_form(info.model,
                            base_class=form.BaseForm,
                            only=info.form_columns,
                            exclude=exclude,
                            field_args=info.form_args,
                            allow_pk=True,
                            converter=converter)

        prop_name = 'fa_%s' % model.__name__

        setattr(form_class,
                prop_name,
                InlineModelFormList(child_form,
                                    info.model,
                                    reverse_field.name,
                                    label=info.model.__name__))

        setattr(field.to,
                prop_name,
                property(lambda self: self.id))

    return form_class


def save_inline(form, model):
    for _, f in form._fields.iteritems():
        if f.type == 'InlineModelFormList':
            f.save_related(model)
