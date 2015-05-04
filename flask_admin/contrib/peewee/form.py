from wtforms import fields

from peewee import (CharField, DateTimeField, DateField, TimeField,
                    PrimaryKeyField, ForeignKeyField, BaseModel)

from wtfpeewee.orm import ModelConverter, model_form

from flask_admin import form
from flask_admin._compat import iteritems, itervalues
from flask_admin.model.form import InlineFormAdmin, InlineModelConverterBase
from flask_admin.model.fields import InlineModelFormField, InlineFieldList, AjaxSelectField

from .tools import get_primary_key
from .ajax import create_ajax_loader


class InlineModelFormList(InlineFieldList):
    """
        Customized inline model form list field.
    """

    form_field_type = InlineModelFormField
    """
        Form field type. Override to use custom field for each inline form
    """

    def __init__(self, form, model, prop, inline_view, **kwargs):
        self.form = form
        self.model = model
        self.prop = prop
        self.inline_view = inline_view

        self._pk = get_primary_key(model)
        super(InlineModelFormList, self).__init__(self.form_field_type(form, self._pk), **kwargs)

    def display_row_controls(self, field):
        return field.get_pk() is not None

    # *** bryhoyt removed def process() entirely, because I believe it was buggy
    # (but worked because another part of the code had a complimentary bug)
    # and I'm not sure why it was necessary anyway.
    # If we want it back in, we need to fix the following bogus query:
    # self.model.select().where(attr == data).execute()     # `data` is not an ID, and only happened to be so because we patched it in in .contribute() below
    #
    # For reference:
    # .process() introduced in https://github.com/flask-admin/flask-admin/commit/2845e4b28cb40b25e2bf544b327f6202dc7e5709
    # Fixed, brokenly I think, in https://github.com/flask-admin/flask-admin/commit/4383eef3ce7eb01878f086928f8773adb9de79f8#diff-f87e7cd76fb9bc48c8681b24f238fb13R30

    def populate_obj(self, obj, name):
        pass

    def save_related(self, obj):
        model_id = getattr(obj, self._pk)

        attr = getattr(self.model, self.prop)
        values = self.model.select().where(attr == model_id).execute()

        pk_map = dict((str(getattr(v, self._pk)), v) for v in values)

        # Handle request data
        for field in self.entries:
            field_id = field.get_pk()

            if field_id in pk_map:
                model = pk_map[field_id]

                if self.should_delete(field):
                    model.delete_instance(recursive=True)
                    continue
            else:
                model = self.model()

            field.populate_obj(model, None)

            # Force relation
            setattr(model, self.prop, model_id)

            self.inline_view.on_model_change(field, model)

            model.save()


class CustomModelConverter(ModelConverter):
    def __init__(self, view, additional=None):
        super(CustomModelConverter, self).__init__(additional)
        self.view = view

        # @todo: This really should be done within wtfpeewee
        self.defaults[CharField] = fields.StringField

        self.converters[PrimaryKeyField] = self.handle_pk
        self.converters[DateTimeField] = self.handle_datetime
        self.converters[DateField] = self.handle_date
        self.converters[TimeField] = self.handle_time

        self.overrides = getattr(self.view, 'form_overrides', None) or {}

    def handle_foreign_key(self, model, field, **kwargs):
        loader = getattr(self.view, '_form_ajax_refs', {}).get(field.name)

        if loader:
            if field.null:
                kwargs['allow_blank'] = True

            return field.name, AjaxSelectField(loader, **kwargs)

        return super(CustomModelConverter, self).handle_foreign_key(model, field, **kwargs)

    def handle_pk(self, model, field, **kwargs):
        kwargs['validators'] = []
        return field.name, fields.HiddenField(**kwargs)

    def handle_date(self, model, field, **kwargs):
        kwargs['widget'] = form.DatePickerWidget()
        return field.name, fields.DateField(**kwargs)

    def handle_datetime(self, model, field, **kwargs):
        kwargs['widget'] = form.DateTimePickerWidget()
        return field.name, fields.DateTimeField(**kwargs)

    def handle_time(self, model, field, **kwargs):
        return field.name, form.TimeField(**kwargs)


def get_form(model, converter,
             base_class=form.BaseForm,
             only=None,
             exclude=None,
             field_args=None,
             allow_pk=False,
             extra_fields=None):
    """
        Create form from peewee model and contribute extra fields, if necessary
    """
    result = model_form(model,
                        base_class=base_class,
                        only=only,
                        exclude=exclude,
                        field_args=field_args,
                        allow_pk=allow_pk,
                        converter=converter)

    if extra_fields:
        for name, field in iteritems(extra_fields):
            setattr(result, name, form.recreate_field(field))

    return result


class InlineModelConverter(InlineModelConverterBase):
    """
        Inline model form helper.
    """

    inline_field_list_type = InlineModelFormList
    """
        Used field list type.

        If you want to do some custom rendering of inline field lists,
        you can create your own wtforms field and use it instead
    """

    def get_info(self, p):
        info = super(InlineModelConverter, self).get_info(p)

        if info is None:
            if isinstance(p, BaseModel):
                info = InlineFormAdmin(p)
            else:
                model = getattr(p, 'model', None)
                if model is None:
                    raise Exception('Unknown inline model admin: %s' % repr(p))

                attrs = dict()

                for attr in dir(p):
                    if not attr.startswith('_') and attr != 'model':
                        attrs[attr] = getattr(p, attr)

                info = InlineFormAdmin(model, **attrs)

        # Resolve AJAX FKs
        info._form_ajax_refs = self.process_ajax_refs(info)

        return info

    def process_ajax_refs(self, info):
        refs = getattr(info, 'form_ajax_refs', None)

        result = {}

        if refs:
            for name, opts in iteritems(refs):
                new_name = '%s.%s' % (info.model.__name__.lower(), name)

                loader = None
                if isinstance(opts, (list, tuple)):
                    loader = create_ajax_loader(info.model, new_name, name, opts)
                else:
                    loader = opts

                result[name] = loader
                self.view._form_ajax_refs[new_name] = loader

        return result

    def contribute(self, converter, model, form_class, inline_model):
        # Find property from target model to current model
        reverse_field = None

        info = self.get_info(inline_model)

        for field in info.model._meta.get_fields():
            field_type = type(field)

            if field_type == ForeignKeyField:
                if field.rel_model == model:
                    reverse_field = field
                    break
        else:
            raise Exception('Cannot find reverse relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_field.name]

        if info.form_excluded_columns:
            exclude = ignore + info.form_excluded_columns
        else:
            exclude = ignore

        # Create field
        child_form = info.get_form()

        if child_form is None:
            child_form = model_form(info.model,
                                    base_class=form.BaseForm,
                                    only=info.form_columns,
                                    exclude=exclude,
                                    field_args=info.form_args,
                                    allow_pk=True,
                                    converter=converter)


        prop_name = reverse_field.related_name

        label = self.get_label(info, prop_name)

        setattr(form_class,
                prop_name,
                self.inline_field_list_type(child_form,
                                            info.model,
                                            reverse_field.name,
                                            info,
                                            label=label or info.model.__name__))

        return form_class


def save_inline(form, model):
    for f in itervalues(form._fields):
        if f.type == 'InlineModelFormList':
            f.save_related(model)
