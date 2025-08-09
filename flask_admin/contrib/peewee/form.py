import typing as t

from peewee import CharField
from peewee import DateField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import ModelBase
from peewee import PrimaryKeyField
from peewee import TimeField
from wtforms import Field
from wtforms import fields
from wtforms.form import BaseForm
from wtforms.form import Form
from wtfpeewee.orm import model_form
from wtfpeewee.orm import ModelConverter

from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin._compat import itervalues
from flask_admin.model.fields import AjaxSelectField
from flask_admin.model.fields import InlineFieldList
from flask_admin.model.fields import InlineModelFormField
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.form import InlineModelConverterBase

from ..._types import T_MODEL_VIEW
from ..._types import T_PEEWEE_MODEL
from .ajax import create_ajax_loader
from .tools import get_meta_fields
from .tools import get_primary_key

try:
    from playhouse.postgres_ext import BinaryJSONField
    from playhouse.postgres_ext import JSONField

    pg_ext = True
except ImportError:
    pg_ext = False


class InlineModelFormList(InlineFieldList):
    """
    Customized inline model form list field.
    """

    form_field_type = InlineModelFormField
    """
        Form field type. Override to use custom field for each inline form
    """

    def __init__(
        self,
        form: type[BaseForm],
        model: type[T_PEEWEE_MODEL],
        prop: t.Any,
        inline_view: T_MODEL_VIEW,
        **kwargs: t.Any,
    ) -> None:
        self.form = form
        self.model = model
        self.prop = prop
        self.inline_view = inline_view

        self._pk = get_primary_key(model)
        super().__init__(self.form_field_type(form, self._pk), **kwargs)

    def display_row_controls(self, field: InlineModelFormField) -> bool:
        return field.get_pk() is not None

    """ bryhoyt removed def process() entirely, because I believe it was buggy
        (but worked because another part of the code had a complimentary bug)
        and I'm not sure why it was necessary anyway.

        If we want it back in, we need to fix the following bogus query:
        self.model.select().where(attr == data).execute()

        `data` is not an ID, and only happened to be so because we patched it
        in in .contribute() below

        For reference, .process() introduced in:
        https://github.com/pallets-eco/flask-admin/commit/2845e4b28cb40b25e2bf544b327f6202dc7e5709

        Fixed, brokenly I think, in:
        https://github.com/pallets-eco/flask-admin/commit/4383eef3ce7eb01878f086928f8773adb9de79f8#diff-f87e7cd76fb9bc48c8681b24f238fb13R30
    """

    def populate_obj(self, obj: t.Any, name: str) -> None:
        pass

    def save_related(self, obj: t.Any) -> None:
        model_id = getattr(obj, self._pk)

        attr = getattr(self.model, self.prop)
        values = self.model.select().where(attr == model_id).execute()

        pk_map = dict((str(getattr(v, self._pk)), v) for v in values)

        # Handle request data
        for field in self.entries:
            field_id = field.get_pk()

            is_created = field_id not in pk_map
            if not is_created:
                model = pk_map[field_id]

                if self.should_delete(field):
                    model.delete_instance(recursive=True)
                    continue
            else:
                model = self.model()

            field.populate_obj(model, None)

            # Force relation
            setattr(model, self.prop, model_id)

            self.inline_view._on_model_change(field, model, is_created)

            model.save()

            # Recurse, to save multi-level nested inlines
            for f in itervalues(field.form._fields):
                if f.type == "InlineModelFormList":
                    f.save_related(model)


class CustomModelConverter(ModelConverter):
    def __init__(self, view: t.Any, additional: t.Any = None) -> None:
        super().__init__(additional)
        self.view = view

        # @todo: This really should be done within wtfpeewee
        self.defaults[CharField] = fields.StringField

        self.converters[PrimaryKeyField] = self.handle_pk
        self.converters[DateTimeField] = self.handle_datetime
        self.converters[DateField] = self.handle_date
        self.converters[TimeField] = self.handle_time

        if pg_ext:
            self.converters[JSONField] = self.handle_json
            self.converters[BinaryJSONField] = self.handle_json

        self.overrides = getattr(self.view, "form_overrides", None) or {}

    def handle_foreign_key(
        self, model: t.Any, field: t.Any, **kwargs: t.Any
    ) -> t.Optional[tuple[str, AjaxSelectField]]:
        loader = getattr(self.view, "_form_ajax_refs", {}).get(field.name)

        if loader:
            if field.null:
                kwargs["allow_blank"] = True

            return field.name, AjaxSelectField(loader, **kwargs)

        return super().handle_foreign_key(model, field, **kwargs)

    def handle_pk(
        self, model: t.Any, field: Field, **kwargs: t.Any
    ) -> tuple[str, fields.HiddenField]:
        kwargs["validators"] = []
        return field.name, fields.HiddenField(**kwargs)

    def handle_date(
        self, model: t.Any, field: Field, **kwargs: t.Any
    ) -> tuple[str, fields.DateField]:
        kwargs["widget"] = form.DatePickerWidget()
        return field.name, fields.DateField(**kwargs)

    def handle_datetime(
        self, model: t.Any, field: Field, **kwargs: t.Any
    ) -> tuple[str, fields.DateTimeField]:
        kwargs["widget"] = form.DateTimePickerWidget()
        return field.name, fields.DateTimeField(**kwargs)

    def handle_time(
        self, model: t.Any, field: Field, **kwargs: t.Any
    ) -> tuple[str, form.TimeField]:
        return field.name, form.TimeField(**kwargs)

    def handle_json(
        self, model: t.Any, field: Field, **kwargs: t.Any
    ) -> tuple[str, form.JSONField]:
        return field.name, form.JSONField(**kwargs)


def get_form(
    model: T_PEEWEE_MODEL,
    converter: CustomModelConverter,
    base_class: type[form.BaseForm] = form.BaseForm,
    only: t.Any = None,
    exclude: t.Any = None,
    field_args: t.Any = None,
    allow_pk: t.Any = None,
    extra_fields: t.Any = None,
) -> type[Form]:
    """
    Create form from peewee model and contribute extra fields, if necessary
    """
    result = model_form(
        model,
        base_class=base_class,
        only=only,
        exclude=exclude,
        field_args=field_args,
        allow_pk=allow_pk,
        converter=converter,
    )

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

    def get_info(
        self,
        p: t.Union[  # type: ignore[override]
            tuple[T_PEEWEE_MODEL, dict[str, t.Any]],
            InlineFormAdmin,
            type[T_PEEWEE_MODEL],
            T_PEEWEE_MODEL,
        ],
    ) -> InlineFormAdmin:
        info = super().get_info(p)  # type: ignore[arg-type]

        if info is None:
            if isinstance(p, ModelBase):
                info = InlineFormAdmin(p)  # type: ignore[arg-type]
            else:
                model = getattr(p, "model", None)
                if model is None:
                    raise Exception(f"Unknown inline model admin: {repr(p)}")

                attrs = dict()

                for attr in dir(p):
                    if not attr.startswith("_") and attr != "model":
                        attrs[attr] = getattr(p, attr)

                info = InlineFormAdmin(model, **attrs)

        # Resolve AJAX FKs
        info._form_ajax_refs = self.process_ajax_refs(info)  # type: ignore[attr-defined]

        return info

    def process_ajax_refs(self, info: InlineFormAdmin) -> dict[str, t.Any]:
        refs = getattr(info, "form_ajax_refs", None)

        result = {}

        if refs:
            for name, opts in iteritems(refs):
                new_name = f"{info.model.__name__.lower()}.{name}"  # type: ignore[union-attr]

                if isinstance(opts, (list, tuple)):
                    loader = create_ajax_loader(
                        info.model,  # type: ignore[arg-type]
                        new_name,
                        name,
                        opts,
                    )
                else:
                    loader = opts

                result[name] = loader
                self.view._form_ajax_refs[new_name] = loader

        return result

    def contribute(
        self,
        converter: t.Any,
        model: t.Any,
        form_class: type[Form],
        inline_model: t.Union[T_PEEWEE_MODEL, InlineFormAdmin],
    ) -> type[Form]:
        # Find property from target model to current model
        reverse_field = None

        info = self.get_info(inline_model)

        for field in get_meta_fields(info.model):  # type: ignore[arg-type]
            field_type = type(field)

            if field_type == ForeignKeyField:
                if field.rel_model == model:  # type: ignore[attr-defined]
                    reverse_field = field
                    break
        else:
            raise Exception(f"Cannot find reverse relation for model {info.model}")

        # Remove reverse property from the list
        ignore = [reverse_field.name]

        if info.form_excluded_columns:  # type: ignore[attr-defined]
            exclude = ignore + info.form_excluded_columns  # type: ignore[attr-defined]
        else:
            exclude = ignore

        # Create field
        child_form = info.get_form()

        if child_form is None:
            child_form = model_form(
                info.model,
                base_class=form.BaseForm,
                only=info.form_columns,  # type: ignore[attr-defined]
                exclude=exclude,
                field_args=info.form_args,  # type: ignore[attr-defined]
                allow_pk=True,
                converter=converter,
            )

        try:
            prop_name = reverse_field.related_name  # type: ignore[attr-defined]
        except AttributeError:
            prop_name = reverse_field.backref  # type: ignore[attr-defined]

        label = self.get_label(info, prop_name)  # type: ignore[arg-type]

        setattr(
            form_class,
            prop_name,
            self.inline_field_list_type(
                child_form,  # type: ignore[arg-type]
                info.model,  # type: ignore[arg-type]
                reverse_field.name,
                info,  # type: ignore[arg-type]
                label=label or info.model.__name__,  # type: ignore[union-attr]
            ),
        )

        return form_class


def save_inline(form: t.Any, model: t.Any) -> None:
    for f in itervalues(form._fields):
        if f.type == "InlineModelFormList":
            f.save_related(model)
