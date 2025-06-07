import typing as t
import warnings
from enum import Enum
from enum import EnumMeta

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy_utils import ChoiceType
from wtforms import Field
from wtforms import fields
from wtforms import Form
from wtforms import HiddenField
from wtforms import validators

from flask_admin import form
from flask_admin._backwards import get_property
from flask_admin._compat import iteritems
from flask_admin._compat import text_type
from flask_admin.model.fields import AjaxSelectField
from flask_admin.model.fields import AjaxSelectMultipleField
from flask_admin.model.fields import InlineFormField
from flask_admin.model.form import converts
from flask_admin.model.form import FieldPlaceholder
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.form import InlineModelConverterBase
from flask_admin.model.form import ModelConverterBase
from flask_admin.model.helpers import prettify_name

from ..._types import T_FIELD_ARGS_FILTERS
from ..._types import T_FIELD_ARGS_LABEL
from ..._types import T_FIELD_ARGS_PLACES
from ..._types import T_FIELD_ARGS_VALIDATORS
from ..._types import T_FIELD_ARGS_VALIDATORS_ALLOW_BLANK
from ..._types import T_MODEL_VIEW
from ..._types import T_ORM_MODEL
from ..._types import T_SQLALCHEMY_INLINE_MODELS
from ..._types import T_SQLALCHEMY_MODEL
from ..._types import T_SQLALCHEMY_SESSION
from ...form import Select2Field
from .ajax import create_ajax_loader
from .fields import HstoreForm
from .fields import InlineHstoreList
from .fields import InlineModelFormList
from .fields import InlineModelOneToOneField
from .fields import QuerySelectField
from .fields import QuerySelectMultipleField
from .tools import filter_foreign_columns
from .tools import get_field_with_path
from .tools import has_multiple_pks
from .tools import is_association_proxy
from .tools import is_relationship
from .validators import TimeZoneValidator
from .validators import Unique
from .validators import valid_color
from .validators import valid_currency


class AdminModelConverter(ModelConverterBase):
    """
    SQLAlchemy model to form converter
    """

    def __init__(self, session: T_SQLALCHEMY_SESSION, view: T_MODEL_VIEW) -> None:
        super().__init__()

        self.session = session
        self.view = view

    def _get_label(self, name: str, field_args: T_FIELD_ARGS_LABEL) -> str:
        """
        Label for field name. If it is not specified explicitly,
        then the views prettify_name method is used to find it.

        :param field_args:
            Dictionary with additional field arguments
        """
        if "label" in field_args:
            return field_args["label"]

        column_labels = get_property(self.view, "column_labels", "rename_columns")

        if column_labels:
            return column_labels.get(name)

        prettify_override = getattr(self.view, "prettify_name", None)
        if prettify_override:
            return prettify_override(name)

        return prettify_name(name)

    def _get_description(
        self, name: str, field_args: T_FIELD_ARGS_VALIDATORS_ALLOW_BLANK
    ) -> t.Optional[str]:
        if "description" in field_args:
            return field_args["description"]

        column_descriptions = getattr(self.view, "column_descriptions", None)

        if column_descriptions:
            return column_descriptions.get(name)
        return None

    def _get_field_override(self, name: str) -> t.Optional[t.Callable]:
        form_overrides = getattr(self.view, "form_overrides", None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def _model_select_field(
        self,
        prop: t.Union[ColumnProperty, InstrumentedAttribute],
        multiple: t.Union[str, bool],
        remote_model: type[T_SQLALCHEMY_MODEL],
        **kwargs: t.Any,
    ) -> t.Union[
        AjaxSelectField,
        AjaxSelectMultipleField,
        QuerySelectMultipleField,
        QuerySelectField,
    ]:
        loader = getattr(self.view, "_form_ajax_refs", {}).get(prop.key)

        if loader:
            if multiple:
                return AjaxSelectMultipleField(loader, **kwargs)
            else:
                return AjaxSelectField(loader, **kwargs)

        if "query_factory" not in kwargs:
            kwargs["query_factory"] = lambda: self.session.query(remote_model)

        if multiple:
            return QuerySelectMultipleField(**kwargs)
        else:
            return QuerySelectField(**kwargs)

    def _convert_relation(
        self,
        name: str,
        prop: t.Any,
        property_is_association_proxy: bool,
        kwargs: T_FIELD_ARGS_VALIDATORS_ALLOW_BLANK,
    ) -> t.Union[
        None,
        AjaxSelectField,
        AjaxSelectMultipleField,
        QuerySelectMultipleField,
        QuerySelectField,
    ]:
        # Check if relation is specified
        form_columns = getattr(self.view, "form_columns", None)
        if form_columns and name not in form_columns:
            return None

        remote_model = prop.mapper.class_
        column = prop.local_remote_pairs[0][0]

        # If this relation points to local column that's not foreign key, assume
        # that it is backref and use remote column data
        if not column.foreign_keys:
            column = prop.local_remote_pairs[0][1]

        kwargs["label"] = self._get_label(name, kwargs)
        kwargs["description"] = self._get_description(name, kwargs)  # type: ignore[typeddict-item]

        # determine optional/required, or respect existing
        requirement_options = (validators.Optional, validators.InputRequired)
        requirement_validator_specified = any(
            isinstance(v, requirement_options) for v in kwargs["validators"]
        )
        if (
            property_is_association_proxy
            or column.nullable
            or prop.direction.name != "MANYTOONE"
        ):
            kwargs["allow_blank"] = True
            if not requirement_validator_specified:
                kwargs["validators"].append(validators.Optional())
        else:
            kwargs["allow_blank"] = False
            if not requirement_validator_specified:
                kwargs["validators"].append(validators.InputRequired())

        # Override field type if necessary
        override = self._get_field_override(prop.key)
        if override:
            return override(**kwargs)

        multiple = property_is_association_proxy or (
            prop.direction.name in ("ONETOMANY", "MANYTOMANY") and prop.uselist
        )
        return self._model_select_field(prop, multiple, remote_model, **kwargs)

    def convert(
        self,
        model: type[T_SQLALCHEMY_MODEL],
        mapper: t.Any,
        name: str,
        prop: t.Union[FieldPlaceholder, ColumnProperty, InstrumentedAttribute],
        field_args: T_FIELD_ARGS_VALIDATORS,
        hidden_pk: bool,
    ) -> t.Union[
        None,
        AjaxSelectField,
        AjaxSelectMultipleField,
        QuerySelectMultipleField,
        QuerySelectField,
        HiddenField,
        Select2Field,
    ]:
        # Properly handle forced fields
        if isinstance(prop, FieldPlaceholder):
            return form.recreate_field(prop.field)

        kwargs: T_FIELD_ARGS_VALIDATORS_ALLOW_BLANK = {"validators": [], "filters": []}

        if field_args:
            kwargs.update(field_args)  # type: ignore[typeddict-item]

        if kwargs["validators"]:
            # Create a copy of the list since we will be modifying it.
            kwargs["validators"] = list(kwargs["validators"])

        # Check if it is relation or property
        if hasattr(prop, "direction") or is_association_proxy(prop):
            property_is_association_proxy = is_association_proxy(prop)
            if property_is_association_proxy:
                if not hasattr(prop.remote_attr, "prop"):
                    raise Exception(
                        "Association proxy referencing another association proxy is "
                        "not supported."
                    )
                prop = prop.remote_attr.prop
            return self._convert_relation(
                name, prop, property_is_association_proxy, kwargs
            )
        elif hasattr(prop, "columns"):  # Ignore pk/fk
            # Check if more than one column mapped to the property
            if len(prop.columns) > 1 and not isinstance(prop, ColumnProperty):
                columns = filter_foreign_columns(
                    model.__table__,  # type: ignore[attr-defined]
                    prop.columns,
                )

                if len(columns) == 0:
                    return None
                elif len(columns) > 1:
                    warnings.warn(
                        (
                            f"Can not convert multiple-column properties"
                            f" ({model}.{prop.key})"
                        ),
                        stacklevel=1,
                    )
                    return None

                column = columns[0]
            else:
                # Grab column
                column = prop.columns[0]

            form_columns = getattr(self.view, "form_columns", None) or ()

            # Do not display foreign keys - use relations, except when explicitly
            # instructed
            if column.foreign_keys and prop.key not in form_columns:
                return None

            # Only display "real" columns
            if not isinstance(column, Column):
                return None

            unique = False

            if column.primary_key:
                if hidden_pk:
                    # If requested to add hidden field, show it
                    return fields.HiddenField()
                else:
                    # By default, don't show primary keys either
                    # If PK is not explicitly allowed, ignore it
                    if prop.key not in form_columns:
                        return None

                    # Current Unique Validator does not work with multicolumns-pks
                    if not has_multiple_pks(model):
                        kwargs["validators"].append(Unique(self.session, model, column))
                        unique = True

            # If field is unique, validate it
            if column.unique and not unique:
                kwargs["validators"].append(Unique(self.session, model, column))

            optional_types = getattr(self.view, "form_optional_types", (Boolean,))

            if (
                not column.nullable
                and not isinstance(column.type, optional_types)
                and not column.default
                and not column.server_default
            ):
                kwargs["validators"].append(validators.InputRequired())

            # Apply label and description if it isn't inline form field
            if self.view.model == mapper.class_:
                kwargs["label"] = self._get_label(prop.key, kwargs)
                kwargs["description"] = self._get_description(  # type: ignore[typeddict-item]
                    prop.key, kwargs
                )

            # Figure out default value
            default = getattr(column, "default", None)
            value = None

            if default is not None:
                value = getattr(default, "arg", None)

                if value is not None:
                    if getattr(default, "is_callable", False):
                        value = lambda: default.arg(None)  # noqa: E731
                    else:
                        if not getattr(default, "is_scalar", True):
                            value = None

            if value is not None:
                kwargs["default"] = value

            # Check nullable
            if column.nullable:
                kwargs["validators"].append(validators.Optional())

            # Override field type if necessary
            override = self._get_field_override(prop.key)
            if override:
                return override(**kwargs)

            # Check if a list of 'form_choices' are specified
            form_choices = getattr(self.view, "form_choices", None)
            if mapper.class_ == self.view.model and form_choices:
                choices = form_choices.get(prop.key)
                if choices:
                    return form.Select2Field(  # type: ignore[misc]
                        choices=choices, allow_blank=column.nullable, **kwargs
                    )

            # Run converter
            converter = self.get_converter(column)

            if converter is None:
                return None

            return converter(
                model=model, mapper=mapper, prop=prop, column=column, field_args=kwargs
            )
        return None

    @classmethod
    def _nullable_common(
        cls,
        column: Column,
        field_args: t.Union[T_FIELD_ARGS_FILTERS, T_FIELD_ARGS_VALIDATORS],
    ) -> None:
        if column.nullable:
            filters = field_args.get("filters", [])
            filters.append(lambda x: x or None)
            field_args["filters"] = filters

    @classmethod
    def _string_common(
        cls,
        column: Column,
        field_args: T_FIELD_ARGS_VALIDATORS,
        **extra: t.Any,
    ) -> None:
        if (
            hasattr(column.type, "length")
            and isinstance(column.type.length, int)
            and column.type.length
        ):
            field_args["validators"].append(validators.Length(max=column.type.length))
        cls._nullable_common(column, field_args)

    @converts("String")  # includes VARCHAR, CHAR, and Unicode
    def conv_String(
        self,
        column: Column,
        field_args: T_FIELD_ARGS_VALIDATORS,
        **extra: t.Any,
    ) -> fields.StringField:
        self._string_common(column=column, field_args=field_args, **extra)
        return fields.StringField(**field_args)

    @converts("sqlalchemy.sql.sqltypes.Enum")
    def convert_enum(
        self,
        column: Column,
        field_args: T_FIELD_ARGS_FILTERS,
        **extra: t.Any,
    ) -> form.Select2Field:
        available_choices = [(f, f) for f in column.type.enums]
        accepted_values = [choice[0] for choice in available_choices]

        if column.nullable:
            field_args["allow_blank"] = column.nullable
            accepted_values.append(None)

        self._nullable_common(column, field_args)

        field_args["choices"] = available_choices
        field_args["validators"].append(validators.AnyOf(accepted_values))
        field_args["coerce"] = lambda v: v.name if isinstance(v, Enum) else text_type(v)
        return form.Select2Field(**field_args)  # type: ignore[arg-type]

    @converts("sqlalchemy_utils.types.choice.ChoiceType")
    def convert_choice_type(
        self, column: Column, field_args: T_FIELD_ARGS_FILTERS, **extra: t.Any
    ) -> form.Select2Field:
        available_choices: t.Union[list[Enum], list[tuple[int, str]]] = []
        # choices can either be specified as an enum, or as a list of tuples
        if isinstance(column.type.choices, EnumMeta):
            available_choices = [  # type: ignore[var-annotated]
                (f.value, f.name) for f in column.type.choices
            ]
        else:
            available_choices = column.type.choices
        accepted_values = [
            choice[0] if isinstance(choice, tuple) else choice.value
            for choice in available_choices
        ]

        if column.nullable:
            field_args["allow_blank"] = column.nullable
            accepted_values.append(None)

        self._nullable_common(column, field_args)

        field_args["choices"] = available_choices
        field_args["validators"].append(validators.AnyOf(accepted_values))
        field_args["coerce"] = choice_type_coerce_factory(column.type)
        return form.Select2Field(**field_args)  # type: ignore[arg-type]

    @converts("Text", "LargeBinary", "Binary", "CIText")  # includes UnicodeText
    def conv_Text(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.TextAreaField:
        self._string_common(field_args=field_args, **extra)
        return fields.TextAreaField(**field_args)

    @converts("Boolean", "sqlalchemy.dialects.mssql.base.BIT")
    def conv_Boolean(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.BooleanField:
        return fields.BooleanField(**field_args)

    @converts("Date")
    def convert_date(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.DateField:
        field_args.setdefault("widget", form.DatePickerWidget())
        return fields.DateField(**field_args)

    @converts("DateTime")  # includes TIMESTAMP
    def convert_datetime(
        self,
        field_args: T_FIELD_ARGS_VALIDATORS,
        **extra: t.Any,
    ) -> form.DateTimeField:
        return form.DateTimeField(**field_args)

    @converts("Time")
    def convert_time(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> form.TimeField:
        return form.TimeField(**field_args)

    @converts("sqlalchemy_utils.types.arrow.ArrowType")
    def convert_arrow_time(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> form.DateTimeField:
        return form.DateTimeField(**field_args)

    @converts("sqlalchemy_utils.types.email.EmailType")
    def convert_email(
        self,
        field_args: T_FIELD_ARGS_VALIDATORS,
        column: t.Optional[Column] = None,
        **extra: t.Any,
    ) -> fields.StringField:
        self._nullable_common(column, field_args)  # type: ignore[arg-type]
        field_args["validators"].append(validators.Email())
        return fields.StringField(**field_args)

    @converts("sqlalchemy_utils.types.url.URLType")
    def convert_url(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args["validators"].append(validators.URL())
        field_args["filters"] = [
            avoid_empty_strings
        ]  # don't accept empty strings, or whitespace
        return fields.StringField(**field_args)

    @converts("sqlalchemy_utils.types.ip_address.IPAddressType")
    def convert_ip_address(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args["validators"].append(validators.IPAddress())
        return fields.StringField(**field_args)

    @converts("sqlalchemy_utils.types.color.ColorType")
    def convert_color(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args["validators"].append(valid_color)
        field_args["filters"] = [
            avoid_empty_strings
        ]  # don't accept empty strings, or whitespace
        return fields.StringField(**field_args)

    @converts("sqlalchemy_utils.types.currency.CurrencyType")
    def convert_currency(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args["validators"].append(valid_currency)
        field_args["filters"] = [
            avoid_empty_strings
        ]  # don't accept empty strings, or whitespace
        return fields.StringField(**field_args)

    @converts("sqlalchemy_utils.types.timezone.TimezoneType")
    def convert_timezone(
        self, column: Column, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args["validators"].append(
            TimeZoneValidator(coerce_function=column.type._coerce)
        )
        return fields.StringField(**field_args)

    @converts("Integer")  # includes BigInteger and SmallInteger
    def handle_integer_types(
        self, column: Column, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.IntegerField:
        unsigned = getattr(column.type, "unsigned", False)
        if unsigned:
            field_args["validators"].append(validators.NumberRange(min=0))
        return fields.IntegerField(**field_args)

    @converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    def handle_decimal_types(
        self, column: t.Any, field_args: T_FIELD_ARGS_PLACES, **extra: t.Any
    ) -> fields.DecimalField:
        # override default decimal places limit, use database defaults instead
        field_args.setdefault("places", None)
        return fields.DecimalField(**field_args)

    @converts("sqlalchemy.dialects.postgresql.base.INET")
    def conv_PGInet(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args.setdefault("label", "IP Address")
        field_args["validators"].append(validators.IPAddress())
        return fields.StringField(**field_args)

    @converts("sqlalchemy.dialects.postgresql.base.MACADDR")
    def conv_PGMacaddr(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args.setdefault("label", "MAC Address")
        field_args["validators"].append(validators.MacAddress())
        return fields.StringField(**field_args)

    @converts(
        "sqlalchemy.dialects.postgresql.base.UUID",
        "sqlalchemy_utils.types.uuid.UUIDType",
    )
    def conv_PGUuid(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> fields.StringField:
        field_args.setdefault("label", "UUID")
        field_args["validators"].append(validators.UUID())
        field_args["filters"] = [
            avoid_empty_strings
        ]  # don't accept empty strings, or whitespace
        return fields.StringField(**field_args)

    @converts(
        "sqlalchemy.dialects.postgresql.base.ARRAY", "sqlalchemy.sql.sqltypes.ARRAY"
    )
    def conv_ARRAY(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> form.Select2TagsField:
        return form.Select2TagsField(save_as_list=True, **field_args)

    @converts("HSTORE")
    def conv_HSTORE(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> InlineHstoreList:
        inner_form = field_args.pop("form", HstoreForm)  # type: ignore[typeddict-item]
        return InlineHstoreList(InlineFormField(inner_form), **field_args)

    @converts("JSON")
    def convert_JSON(
        self, field_args: T_FIELD_ARGS_VALIDATORS, **extra: t.Any
    ) -> form.JSONField:
        return form.JSONField(**field_args)


def avoid_empty_strings(value: t.Any) -> t.Any:
    """
    Return None if the incoming value is an empty string or whitespace.
    """
    if value:
        try:
            value = value.strip()
        except AttributeError:
            # values are not always strings
            pass
    return value if value else None


def choice_type_coerce_factory(type_: ChoiceType) -> t.Callable[[t.Any], t.Any]:
    """
    Return a function to coerce a ChoiceType column, for use by Select2Field.
    :param type_: ChoiceType object
    """
    from sqlalchemy_utils import Choice

    choices = type_.choices
    if isinstance(choices, type) and issubclass(choices, Enum):
        key, choice_cls = "value", choices
    else:
        key, choice_cls = "code", Choice

    def choice_coerce(value: t.Any) -> t.Any:
        if value is None:
            return None
        if isinstance(value, choice_cls):
            return getattr(value, key)
        return type_.python_type(value)

    return choice_coerce


def _resolve_prop(prop: ColumnProperty) -> ColumnProperty:
    """
    Resolve proxied property

    :param prop:
        Property to resolve
    """
    # Try to see if it is proxied property
    if hasattr(prop, "_proxied_property"):
        return prop._proxied_property

    return prop


# Get list of fields and generate form
def get_form(
    model: type[T_SQLALCHEMY_MODEL],
    converter: AdminModelConverter,
    base_class: type[form.BaseForm] = form.BaseForm,
    only: t.Optional[t.Collection[t.Union[str, InstrumentedAttribute]]] = None,
    exclude: t.Optional[t.Collection[t.Union[str, InstrumentedAttribute]]] = None,
    field_args: t.Optional[dict[str, T_FIELD_ARGS_VALIDATORS]] = None,
    hidden_pk: bool = False,
    ignore_hidden: bool = True,
    extra_fields: t.Optional[dict[t.Union[str, InstrumentedAttribute], Field]] = None,
) -> type:
    """
    Generate form from the model.

    :param model:
        Model to generate form from
    :param converter:
        Converter class to use
    :param base_class:
        Base form class
    :param only:
        Include fields
    :param exclude:
        Exclude fields
    :param field_args:
        Dictionary with additional field arguments
    :param hidden_pk:
        Generate hidden field with model primary key or not
    :param ignore_hidden:
        If set to True (default), will ignore properties that start with underscore
    """

    # TODO: Support new 0.8 API
    if not hasattr(model, "_sa_class_manager"):
        raise TypeError("model must be a sqlalchemy mapped model")

    mapper = model._sa_class_manager.mapper
    field_args = field_args or {}

    properties = ((p.key, p) for p in mapper.attrs)

    if only:

        def find(
            name: t.Union[str, InstrumentedAttribute],
        ) -> t.Union[
            tuple[str, FieldPlaceholder],
            tuple[str, t.Optional[t.Any]],
            tuple[t.Any, t.Any],
        ]:
            # If field is in extra_fields, it has higher priority
            if extra_fields and name in extra_fields:
                return name, FieldPlaceholder(extra_fields[name])

            column, path = get_field_with_path(
                model, name, return_remote_proxy_attr=False
            )
            column = t.cast(InstrumentedAttribute, column)
            if path and not (is_relationship(column) or is_association_proxy(column)):
                raise Exception(
                    "form column is located in another table and "
                    f"requires inline_models: {name}"
                )

            if is_association_proxy(column):
                return name, column

            relation_name = column.key

            if column is not None and hasattr(column, "property"):
                return relation_name, column.property

            raise ValueError(f"Invalid model property name {model}.{name}")

        # Filter properties while maintaining property order in 'only' list
        properties = (find(x) for x in only)
    elif exclude:
        properties = (x for x in properties if x[0] not in exclude)

    field_dict = {}
    for name, p in properties:
        # Ignore protected properties
        if ignore_hidden and name.startswith("_"):
            continue

        prop = _resolve_prop(p)

        field = converter.convert(
            model,
            mapper,
            name,
            prop,
            field_args.get(name),  # type: ignore[arg-type]
            hidden_pk,
        )
        if field is not None:
            field_dict[name] = field

    # Contribute extra fields
    if not only and extra_fields:
        for name, field in iteritems(extra_fields):
            field_dict[name] = form.recreate_field(field)

    return type(model.__name__ + "Form", (base_class,), field_dict)


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

    def __init__(
        self,
        session: T_SQLALCHEMY_SESSION,
        view: T_MODEL_VIEW,
        model_converter: t.Callable[[T_SQLALCHEMY_SESSION, t.Any], t.Any],
    ) -> None:
        """
        Constructor.

        :param session:
            SQLAlchemy session
        :param view:
            Flask-Admin view object
        :param model_converter:
            Model converter class. Will be automatically instantiated with
            appropriate `InlineFormAdmin` instance.
        """
        super().__init__(view)
        self.session = session
        self.model_converter = model_converter

    def get_info(
        self,
        p: t.Union[
            tuple[T_ORM_MODEL, dict[str, t.Any]], InlineFormAdmin, type[T_ORM_MODEL]
        ],
    ) -> InlineFormAdmin:
        info = super().get_info(p)

        # Special case for model instances
        if info is None:
            if hasattr(p, "_sa_class_manager"):
                return self.form_admin_class(p)
            else:
                model = getattr(p, "model", None)

                if model is None:
                    raise Exception(f"Unknown inline model admin: {repr(p)}")

                attrs = dict()
                for attr in dir(p):
                    if not attr.startswith("_") and attr != "model":
                        attrs[attr] = getattr(p, attr)

                return self.form_admin_class(model, **attrs)

            info = self.form_admin_class(model, **attrs)

        # Resolve AJAX FKs
        info._form_ajax_refs = self.process_ajax_refs(info)  # type: ignore[attr-defined]

        return info

    def process_ajax_refs(self, info: InlineFormAdmin) -> dict:
        refs = getattr(info, "form_ajax_refs", None)

        result = {}

        if refs:
            for name, opts in iteritems(refs):
                new_name = f"{info.model.__name__.lower()}-{name}"  # type: ignore[union-attr]

                loader = None
                if isinstance(opts, dict):
                    loader = create_ajax_loader(
                        info.model, self.session, new_name, name, opts
                    )
                else:
                    loader = opts
                    # If we're changing the name in self.view._form_ajax_refs,
                    # we must also change loader.name property. Otherwise
                    # when the widget tries to set the 'data-url' property in the
                    # <input> tag, it won't be able to find the loader since it'll be
                    # using the "field.loader.name" of the previously-configured loader.
                    loader.name = new_name

                result[name] = loader
                self.view._form_ajax_refs[new_name] = loader

        return result

    def _calculate_mapping_key_pair(
        self, model: type[T_SQLALCHEMY_MODEL], info: InlineFormAdmin
    ) -> dict[str, str]:
        """
        Calculate mapping property key pair between `model` and inline model,
            including the forward one for `model` and the reverse one for inline model.
            Override the method to map your own inline models.

        :param model:
            Model class
        :param info:
            The InlineFormAdmin instance
        :return:
            A dict of forward property key and reverse property key
        """
        mapper = model._sa_class_manager.mapper  # type: ignore[attr-defined]

        # Find property from target model to current model
        # Use the base mapper to support inheritance
        target_mapper = info.model._sa_class_manager.mapper.base_mapper  # type: ignore[union-attr]

        reverse_props = []
        forward_reverse_props_keys: dict[str, str] = dict()
        for prop in target_mapper.iterate_properties:  # type: ignore[misc]
            if hasattr(prop, "direction") and prop.direction.name in (
                "MANYTOONE",
                "MANYTOMANY",
            ):
                if issubclass(model, prop.mapper.class_):
                    # store props in reverse_props list
                    reverse_props.append(prop)

        if not reverse_props:
            raise Exception(f"Cannot find reverse relation for model {info.model}")

        for reverse_prop in reverse_props:
            # Find forward property

            if reverse_prop.direction.name == "MANYTOONE":
                candidate = "ONETOMANY"
            else:
                candidate = "MANYTOMANY"

            for prop in mapper.iterate_properties:
                if hasattr(prop, "direction") and prop.direction.name == candidate:
                    # check if prop is not handled yet
                    # issubclass is more useful than equal comparator in the case
                    # of inheritance
                    if prop.key not in forward_reverse_props_keys.keys() and issubclass(
                        target_mapper.class_,  # type: ignore[arg-type]
                        prop.mapper.class_,
                    ):
                        forward_reverse_props_keys[prop.key] = reverse_prop.key
                        break
            else:
                raise Exception(f"Cannot find forward relation for model {info.model}")

        return forward_reverse_props_keys

    def contribute(
        self,
        model: type[T_SQLALCHEMY_MODEL],
        form_class: type[Form],
        inline_model: T_SQLALCHEMY_INLINE_MODELS,
    ) -> type[Form]:
        """
        Generate form fields for inline forms and contribute them to
        the `form_class`

        :param converter:
            ModelConverterBase instance
        :param session:
            SQLAlchemy session
        :param model:
            Model class
        :param form_class:
            Form to add properties to
        :param inline_model:
            Inline model. Can be one of:

             - ``tuple``, first value is related model instance,
             second is dictionary with options
             - ``InlineFormAdmin`` instance
             - Model class

        :return:
            Form class
        """

        info = t.cast(T_MODEL_VIEW, self.get_info(inline_model))  # type: ignore[arg-type]
        forward_reverse_props_keys: dict = self._calculate_mapping_key_pair(
            model,
            info,  # type: ignore[arg-type]
        )

        for forward_prop_key, reverse_prop_key in forward_reverse_props_keys.items():
            # Remove reverse property from the list
            ignore = [reverse_prop_key]

            if info.form_excluded_columns:
                exclude = ignore + list(info.form_excluded_columns)
            else:
                exclude = ignore

            # Create converter
            converter = self.model_converter(self.session, info)

            # Create form
            child_form = info.get_form()

            if child_form is None:
                child_form = get_form(
                    info.model,
                    converter,
                    base_class=info.form_base_class or form.BaseForm,
                    only=info.form_columns,
                    exclude=exclude,
                    field_args=info.form_args,
                    hidden_pk=True,
                    extra_fields=info.form_extra_fields,
                )

            # Post-process form
            child_form = info.postprocess_form(child_form)  # type: ignore[attr-defined]

            kwargs = dict()

            label = self.get_label(info, forward_prop_key)
            if label:
                kwargs["label"] = label

            if self.view.form_args:
                field_args = t.cast(dict, self.view.form_args.get(forward_prop_key, {}))
                kwargs.update(**field_args)

            # Contribute field
            setattr(
                form_class,
                forward_prop_key,
                self.inline_field_list_type(
                    child_form,
                    self.session,
                    info.model,  # type: ignore[arg-type]
                    reverse_prop_key,
                    info,
                    **kwargs,
                ),
            )

        return form_class


class InlineOneToOneModelConverter(InlineModelConverter):
    inline_field_list_type = InlineModelOneToOneField  # type: ignore[assignment]

    def _calculate_mapping_key_pair(
        self, model: type[T_SQLALCHEMY_MODEL], info: InlineFormAdmin
    ) -> dict[str, str]:
        mapper = info.model._sa_class_manager.mapper.base_mapper  # type: ignore[union-attr]
        target_mapper = model._sa_class_manager.mapper  # type: ignore[attr-defined]

        inline_relationship = dict()

        for forward_prop in mapper.iterate_properties:  # type: ignore[misc]
            if not hasattr(forward_prop, "direction"):
                continue

            if forward_prop.direction.name != "MANYTOONE":
                continue

            if forward_prop.mapper.class_ != target_mapper.class_:
                continue

            # in case when model has few relationships to target model or
            # has just installed references manually. This is more quick
            # solution rather than rotate yet another one loop
            ref = forward_prop.backref

            if not ref:
                ref = forward_prop.back_populates

            if ref:
                inline_relationship[ref] = forward_prop.key
                continue

            # here we suppose that model has only one relationship
            # to target model and prop has not t.Any reference
            for backward_prop in target_mapper.iterate_properties:
                if not hasattr(backward_prop, "direction"):
                    continue

                if backward_prop.direction.name != "ONETOMANY":
                    continue

                if issubclass(model, backward_prop.mapper.class_):
                    inline_relationship[backward_prop.key] = forward_prop.key
                    break
            else:
                raise Exception(f"Cannot find reverse relation for model {info.model}")
            break

        if not inline_relationship:
            raise Exception(f"Cannot find forward relation for model {info.model}")

        return inline_relationship

    def contribute(
        self,
        model: t.Any,
        form_class: type[Form],
        inline_model: T_SQLALCHEMY_INLINE_MODELS,
    ) -> type[Form]:
        info = t.cast(T_MODEL_VIEW, self.get_info(inline_model))  # type: ignore[arg-type]

        inline_relationships = self._calculate_mapping_key_pair(
            model,
            info,  # type: ignore[arg-type]
        )

        # Remove reverse property from the list
        ignore: list[str] = [value for value in inline_relationships.values()]

        if info.form_excluded_columns:
            exclude = ignore + list(info.form_excluded_columns)
        else:
            exclude = ignore

        # Create converter
        converter = self.model_converter(self.session, info)

        # Create form
        child_form = info.get_form()

        if child_form is None:
            child_form = get_form(
                info.model,
                converter,
                base_class=info.form_base_class or form.BaseForm,
                only=info.form_columns,
                exclude=exclude,
                field_args=info.form_args,
                hidden_pk=True,
                extra_fields=info.form_extra_fields,
            )

        # Post-process form
        child_form = info.postprocess_form(child_form)  # type: ignore[attr-defined]

        kwargs: dict = dict()

        # Contribute field
        for key in inline_relationships.keys():
            setattr(
                form_class,
                key,
                self.inline_field_list_type(
                    child_form,
                    self.session,
                    info.model,
                    inline_relationships[key],
                    info,  # type: ignore[arg-type]
                    **kwargs,
                ),
            )

        return form_class
