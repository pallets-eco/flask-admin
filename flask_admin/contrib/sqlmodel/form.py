"""
SQLModel form generation and field conversion utilities.

This module provides form generation capabilities for SQLModel models,
including automatic field conversion from SQLModel types to WTForms fields,
and support for inline models and relationships.
"""

import warnings
from enum import Enum
from typing import Any
from typing import Optional

from sqlmodel import select
from sqlmodel import SQLModel

# Import from sqlalchemy for types not in sqlmodel
try:
    from sqlmodel import Boolean
    from sqlmodel import Column
except ImportError:
    from sqlalchemy import Boolean
    from sqlalchemy import Column

from sqlalchemy.orm import ColumnProperty
from wtforms import fields
from wtforms import validators

from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin._compat import text_type
from flask_admin.form import BaseForm
from flask_admin.model.fields import AjaxSelectField
from flask_admin.model.fields import AjaxSelectMultipleField
from flask_admin.model.fields import InlineFormField
from flask_admin.model.form import converts
from flask_admin.model.form import FieldPlaceholder
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.form import InlineModelConverterBase
from flask_admin.model.form import ModelConverterBase
from flask_admin.model.helpers import prettify_name

from .ajax import create_ajax_loader
from .fields import HstoreForm
from .fields import InlineHstoreList
from .fields import InlineModelFormList
from .fields import InlineModelOneToOneField
from .fields import QuerySelectField
from .fields import QuerySelectMultipleField
from .mixins import SQLAlchemyExtendedMixin
from .tools import filter_foreign_columns
from .tools import get_computed_fields
from .tools import get_field_with_path
from .tools import has_multiple_pks
from .tools import is_association_proxy
from .tools import is_computed_field
from .tools import is_relationship
from .tools import is_sqlmodel_table
from .validators import Unique


class AdminModelConverter(ModelConverterBase, SQLAlchemyExtendedMixin):
    """
    SQLModel to form converter
    """

    def __init__(self, session, view):
        super().__init__()

        self.session = session
        self.view = view

    def _get_field_class_override(
        self, field_name: str, model_field: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Get field class override for a field,
        checking multiple sources in priority order.

        Priority order:
        1. View-level field type overrides (view.form_overrides)
        2. Field-level field_class from SQLModel Field definition
        3. Type-level converters (handled by parent converter system)

        Args:
            field_name: Name of the field
            model_field: ModelField instance containing field metadata

        Returns:
            WTForms field class if override found, None otherwise
        """
        # 1. Check view-level overrides first (highest priority)
        form_overrides = getattr(self.view, "form_overrides", None)
        if (
            form_overrides
            and hasattr(form_overrides, "__contains__")
            and field_name in form_overrides
        ):
            override_value = form_overrides[field_name]
            # Handle both field class and field instance
            if isinstance(override_value, type):
                return override_value
            elif hasattr(override_value, "__class__"):
                return override_value.__class__

        # 2. Check field-level field_class from SQLModel Field definition
        if (
            model_field
            and hasattr(model_field, "field_class")
            and model_field.field_class
        ):
            return model_field.field_class

        # 3. No override found - will fall back to type-based conversion
        return None

    def _get_label(self, name, field_args):
        """
        Label for field name. If it is not specified explicitly,
        then the views prettify_name method is used to find it.

        :param field_args:
            Dictionary with additional field arguments
        """
        if "label" in field_args:
            return field_args["label"]

        column_labels = getattr(self.view, "column_labels", None)

        if column_labels:
            return column_labels.get(name)

        prettify_override = getattr(self.view, "prettify_name", None)
        if prettify_override:
            return prettify_override(name)

        return prettify_name(name)

    def _get_description(self, name, field_args):
        if "description" in field_args:
            return field_args["description"]

        column_descriptions = getattr(self.view, "column_descriptions", None)

        if column_descriptions:
            return column_descriptions.get(name)

    def _get_field_override(self, name):
        form_overrides = getattr(self.view, "form_overrides", None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def _model_select_field(self, prop, multiple, remote_model, **kwargs):
        loader = getattr(self.view, "_form_ajax_refs", {}).get(prop.key)

        if loader:
            if multiple:
                return AjaxSelectMultipleField(loader, **kwargs)
            else:
                return AjaxSelectField(loader, **kwargs)

        if "query_factory" not in kwargs:
            kwargs["query_factory"] = lambda: self.session.exec(select(remote_model))

        if multiple:
            return QuerySelectMultipleField(**kwargs)
        else:
            return QuerySelectField(**kwargs)

    def _convert_relation(self, name, prop, property_is_association_proxy, kwargs):
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
        kwargs["description"] = self._get_description(name, kwargs)

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

    def _convert_computed_field(self, model, name, field_info, kwargs):
        """
        Convert SQLModel computed field to form field.
        Enhanced to support computed fields with setters for WTForms compatibility.
        """
        # Check if this computed field has a setter (is WTForms compatible)
        has_setter = False
        return_type = None

        try:
            from .tools import _get_sqlmodel_property_info

            prop_info = _get_sqlmodel_property_info(model, name)
            has_setter = prop_info.get("has_setter", False)
            return_type = prop_info.get("type_")
        except (AttributeError, TypeError, ImportError):
            # Fallback for mocks or when property info can't be retrieved
            has_setter = False
            return_type = None

        # For computed fields, include them only if
        # they have setters or are explicitly requested
        form_columns = getattr(self.view, "form_columns", None)
        if form_columns and name not in form_columns:
            return None
        elif form_columns is None and not has_setter:
            # For backward compatibility with tests/mocks,
            # include fields when form_columns is None
            # but only if we couldn't determine setter status (likely a mock)
            try:
                # Try to check if this is a real SQLModel class
                from .tools import is_sqlmodel_class

                if is_sqlmodel_class(model):
                    # Real SQLModel - exclude computed fields without setters by default
                    return None
            except (AttributeError, TypeError, ImportError):
                pass
            # Fall through to include the field (for mocks/tests)

        # Apply label and description
        kwargs["label"] = self._get_label(name, kwargs)
        kwargs["description"] = self._get_description(name, kwargs)

        # If no setter, make field read-only
        if not has_setter:
            kwargs["render_kw"] = kwargs.get("render_kw", {})
            kwargs["render_kw"]["readonly"] = True

        # Try to determine field type based on the computed field's return type
        if return_type:
            if return_type is int:
                return fields.IntegerField(**kwargs)
            elif return_type is float:
                return fields.DecimalField(**kwargs)
            elif return_type is bool:
                return fields.BooleanField(**kwargs)

        # Override field type if necessary
        override = self._get_field_override(name)
        if override:
            return override(**kwargs)

        # Default to StringField for computed fields
        return fields.StringField(**kwargs)

    def _convert_property_field(self, model, name, property_obj, kwargs):
        """
        Convert SQLModel @property to form field.
        Only includes properties with setters for WTForms compatibility.
        """
        # Get property information with fallback for mocks
        has_setter = False
        return_type = None

        try:
            from .tools import _get_sqlmodel_property_info

            prop_info = _get_sqlmodel_property_info(model, name)
            has_setter = prop_info.get("has_setter", False)
            return_type = prop_info.get("type_")
        except (AttributeError, TypeError, ImportError):
            # Fallback for mocks or when property info can't be retrieved
            has_setter = False
            return_type = None

        # Only include properties with setters (WTForms compatible)
        form_columns = getattr(self.view, "form_columns", None)
        if form_columns and name not in form_columns:
            return None
        elif form_columns is None and not has_setter:
            # By default, exclude properties without setters
            return None

        # Apply label and description
        kwargs["label"] = self._get_label(name, kwargs)
        kwargs["description"] = self._get_description(name, kwargs)

        # If no setter, make field read-only
        if not has_setter:
            kwargs["render_kw"] = kwargs.get("render_kw", {})
            kwargs["render_kw"]["readonly"] = True

        # Try to determine field type based on property's return type annotation
        if return_type:
            if return_type is int:
                return fields.IntegerField(**kwargs)
            elif return_type is float:
                return fields.DecimalField(**kwargs)
            elif return_type is bool:
                return fields.BooleanField(**kwargs)

        # Override field type if necessary
        override = self._get_field_override(name)
        if override:
            return override(**kwargs)

        # Default to StringField for properties
        return fields.StringField(**kwargs)

    def convert(self, model, mapper, name, prop, field_args, hidden_pk):
        # Properly handle forced fields
        if isinstance(prop, FieldPlaceholder):
            return form.recreate_field(prop.field)

        kwargs = {"validators": [], "filters": []}

        if field_args:
            kwargs.update(field_args)

        if kwargs["validators"]:
            # Create a copy of the list since we will be modifying it.
            kwargs["validators"] = list(kwargs["validators"])

        # Check for field class override before type-based conversion
        from .tools import ModelField

        model_field_info = prop if isinstance(prop, ModelField) else None
        field_class_override = self._get_field_class_override(name, model_field_info)
        if field_class_override:
            return field_class_override(**kwargs)

        # Handle SQLModel computed fields
        if issubclass(model, SQLModel) and is_computed_field(model, name):
            computed_fields = get_computed_fields(model)
            field_info = computed_fields.get(name)
            if field_info:
                return self._convert_computed_field(model, name, field_info, kwargs)

        # Handle ModelField objects (properties and computed fields with setters)
        from .tools import ModelField

        if isinstance(prop, ModelField):
            if prop.is_computed:
                return self._convert_computed_field(model, name, prop.source, kwargs)
            elif prop.is_property:
                return self._convert_property_field(model, name, prop.source, kwargs)

        # Check if it is relation or property
        if hasattr(prop, "direction") or is_association_proxy(prop):
            property_is_association_proxy = is_association_proxy(prop)
            if property_is_association_proxy:
                if not hasattr(prop.remote_attr, "prop"):  # type: ignore
                    raise Exception(
                        "Association proxy referencing another association proxy is "
                        "not supported."
                    )
                prop = prop.remote_attr.prop  # type: ignore
            return self._convert_relation(
                name, prop, property_is_association_proxy, kwargs
            )
        elif hasattr(prop, "columns"):  # Ignore pk/fk
            # Check if more than one column mapped to the property
            if len(prop.columns) > 1 and not isinstance(prop, ColumnProperty):  # type: ignore
                columns = filter_foreign_columns(model.__table__, prop.columns)  # type: ignore

                if len(columns) == 0:
                    return None
                elif len(columns) > 1:
                    warnings.warn(
                        (
                            f"Can not convert multiple-column properties"
                            f" ({model}.{prop.key})"  # type: ignore
                        ),
                        stacklevel=1,
                    )
                    return None

                column = columns[0]
            else:
                # Grab column
                column = prop.columns[0]  # type: ignore

            form_columns = getattr(self.view, "form_columns", None) or ()

            # Do not display foreign keys - use relations, except when explicitly
            # instructed
            if column.foreign_keys and prop.key not in form_columns:  # type: ignore
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
                    # Fix: Only exclude primary keys if form_columns is explicitly
                    # set and the key is not in it
                    if (
                        hasattr(self.view, "form_columns")
                        and self.view.form_columns is not None
                        and prop.key not in self.view.form_columns  # type: ignore
                    ):
                        return None

                    # Current Unique Validator does not work with multicolumns-pks
                    if not has_multiple_pks(model):
                        kwargs["validators"].append(Unique(self.session, model, column))
                        unique = True

            # If field is unique, validate it
            if column.unique and not unique:
                kwargs["validators"].append(Unique(self.session, model, column))

            optional_types = getattr(self.view, "form_optional_types", (Boolean,))

            # For SQLModel, also check if field is Optional in the model definition
            if issubclass(model, SQLModel):
                model_fields = getattr(model, "model_fields", {})
                field_info = model_fields.get(prop.key)  # type: ignore
                is_optional = field_info and not field_info.is_required()
            else:
                is_optional = False

            if (
                not column.nullable
                and not is_optional
                and not isinstance(column.type, optional_types)
                and not column.default
                and not column.server_default
            ):
                kwargs["validators"].append(validators.InputRequired())

            # Apply label and description if it isn't inline form field
            if self.view.model == mapper.class_:
                kwargs["label"] = self._get_label(prop.key, kwargs)  # type: ignore
                kwargs["description"] = self._get_description(prop.key, kwargs)  # type: ignore

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

            # For SQLModel, also check for Pydantic field defaults
            if value is None and issubclass(model, SQLModel):
                from pydantic_core import PydanticUndefined

                model_fields = getattr(model, "model_fields", {})
                field_info = model_fields.get(prop.key)  # type: ignore
                if (
                    field_info
                    and field_info.default is not None
                    and field_info.default is not PydanticUndefined
                ):
                    value = field_info.default

            if value is not None:
                kwargs["default"] = value  # type: ignore

            # Check nullable
            if column.nullable or is_optional:
                kwargs["validators"].append(validators.Optional())

            # Override field type if necessary
            override = self._get_field_override(prop.key)  # type: ignore
            if override:
                return override(**kwargs)

            # Check if a list of 'form_choices' are specified
            form_choices = getattr(self.view, "form_choices", None)
            if mapper.class_ == self.view.model and form_choices:
                choices = form_choices.get(prop.key)  # type: ignore
                if choices:
                    # Check if this is an enum field that needs coercion
                    coerce_func = None
                    if issubclass(model, SQLModel):
                        model_fields = getattr(model, "model_fields", {})
                        field_info = model_fields.get(prop.key)  # type: ignore
                        if field_info:
                            # Get the type annotation
                            original_annotation = getattr(
                                model, "__annotations__", {}
                            ).get(prop.key)  # type: ignore
                            pydantic_type = original_annotation or field_info.annotation

                            # Handle Optional types
                            import typing

                            if hasattr(pydantic_type, "__origin__"):
                                origin = pydantic_type.__origin__
                                if origin is typing.Union:
                                    args = getattr(pydantic_type, "__args__", ())
                                    non_none_args = [
                                        arg for arg in args if arg is not type(None)
                                    ]
                                    if len(non_none_args) == 1:
                                        pydantic_type = non_none_args[0]

                            # If it's an enum, provide coercion function
                            if hasattr(pydantic_type, "__members__") and issubclass(
                                pydantic_type, Enum
                            ):

                                def enum_coerce(value):
                                    if value is None or value == "":
                                        return None
                                    if isinstance(value, pydantic_type):
                                        return value.value
                                    return value

                                coerce_func = enum_coerce

                    field_kwargs = {
                        "choices": choices,
                        "allow_blank": column.nullable or is_optional,  # type: ignore
                        **kwargs,  # type: ignore
                    }
                    if coerce_func:
                        field_kwargs["coerce"] = coerce_func

                    return form.Select2Field(**field_kwargs)

            # For SQLModel, check for special Pydantic types first
            if issubclass(model, SQLModel):
                model_fields = getattr(model, "model_fields", {})
                field_info = model_fields.get(prop.key)  # type: ignore
                if field_info:
                    # Get the original annotation from __annotations__
                    # which preserves constrained types
                    original_annotation = getattr(model, "__annotations__", {}).get(
                        prop.key  # type: ignore
                    )
                    pydantic_type = original_annotation or field_info.annotation

                    # Handle Optional types (Union[SomeType, None])
                    import typing

                    if hasattr(pydantic_type, "__origin__"):
                        origin = pydantic_type.__origin__
                        if origin is typing.Union:
                            # This is Optional[SomeType] or SomeType | None
                            args = getattr(pydantic_type, "__args__", ())
                            non_none_args = [
                                arg for arg in args if arg is not type(None)
                            ]
                            if len(non_none_args) == 1:
                                pydantic_type = non_none_args[0]

                    # Check for constrained types first (they take precedence)
                    constrained_field = self.conv_pydantic_constrained_field(
                        model, field_info, pydantic_type, kwargs
                    )
                    if constrained_field:
                        return constrained_field

                    # Check for Python enum types
                    # (only for pure SQLModel fields, not sa_column)
                    if (
                        hasattr(pydantic_type, "__members__")
                        and issubclass(pydantic_type, Enum)
                        and getattr(field_info, "sa_column", None) is None
                    ):
                        return self.conv_python_enum(pydantic_type, column, kwargs)

                    # Try to get converter for the Pydantic type
                    pydantic_type_name = (
                        f"{pydantic_type.__module__}.{pydantic_type.__name__}"
                    )
                    pydantic_converter = self.converters.get(pydantic_type_name)
                    if pydantic_converter:
                        return pydantic_converter(field_args=kwargs, column=column)

            # Try SQLAlchemy-utils extended types (via mixin)
            extended_field = self.handle_extended_types(model, column, kwargs)
            if extended_field:
                return extended_field

            # Run converter
            converter = self.get_converter(column)

            if converter is None:
                return None

            return converter(
                model=model, mapper=mapper, prop=prop, column=column, field_args=kwargs
            )
        return None

    @classmethod
    def _nullable_common(cls, column, field_args):
        if column.nullable:
            filters = field_args.get("filters", [])
            filters.append(lambda x: x or None)
            field_args["filters"] = filters

    @classmethod
    def _string_common(cls, column, field_args, **extra):
        if (
            hasattr(column.type, "length")
            and isinstance(column.type.length, int)
            and column.type.length
        ):
            field_args["validators"].append(validators.Length(max=column.type.length))
        cls._nullable_common(column, field_args)

    @converts("String")  # includes VARCHAR, CHAR, and Unicode
    def conv_String(self, column, field_args, **extra):
        self._string_common(column=column, field_args=field_args, **extra)
        return fields.StringField(**field_args)

    @converts("sqlmodel.sql.sqltypes.AutoString")  # SQLModel AutoString type
    def conv_AutoString(self, column, field_args, **extra):
        self._string_common(column=column, field_args=field_args, **extra)
        return fields.StringField(**field_args)

    @converts("sqlalchemy.sql.sqltypes.Enum")
    def convert_enum(self, column, field_args, **extra):
        available_choices = [(f, f) for f in column.type.enums]
        accepted_values = [choice[0] for choice in available_choices]

        if column.nullable:
            field_args["allow_blank"] = column.nullable
            accepted_values.append(None)

        self._nullable_common(column, field_args)

        field_args["choices"] = available_choices
        field_args["validators"].append(validators.AnyOf(accepted_values))
        field_args["coerce"] = lambda v: v.name if isinstance(v, Enum) else text_type(v)
        return form.Select2Field(**field_args)

    # Note: ChoiceType from sqlalchemy_utils is not supported in pure SQLModel
    # Use Python Enum types instead

    @converts("Text", "LargeBinary", "Binary", "CIText")  # includes UnicodeText
    def conv_Text(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
        return fields.TextAreaField(**field_args)

    @converts("Boolean", "sqlalchemy.dialects.mssql.base.BIT")
    def conv_Boolean(self, field_args, **extra):
        return fields.BooleanField(**field_args)

    @converts("Date")
    def convert_date(self, field_args, **extra):
        field_args.setdefault("widget", form.DatePickerWidget())
        return fields.DateField(**field_args)

    @converts("DateTime")  # includes TIMESTAMP
    def convert_datetime(self, field_args, **extra):
        return form.DateTimeField(**field_args)

    @converts("Time")
    def convert_time(self, field_args, **extra):
        return form.TimeField(**field_args)

    # SQLAlchemy-utils converters have been moved to SQLAlchemyExtendedMixin

    @converts("Integer")  # includes BigInteger and SmallInteger
    def handle_integer_types(self, column, field_args, **extra):
        unsigned = getattr(column.type, "unsigned", False)
        if unsigned:
            field_args["validators"].append(validators.NumberRange(min=0))
        return fields.IntegerField(**field_args)

    @converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    def handle_decimal_types(self, column, field_args, **extra):
        # override default decimal places limit, use database defaults instead
        field_args.setdefault("places", None)
        return fields.DecimalField(**field_args)

    @converts("sqlalchemy.dialects.postgresql.base.INET")
    def conv_PGInet(self, field_args, **extra):
        field_args.setdefault("label", "IP Address")
        field_args["validators"].append(validators.IPAddress())
        return fields.StringField(**field_args)

    @converts("sqlalchemy.dialects.postgresql.base.MACADDR")
    def conv_PGMacaddr(self, field_args, **extra):
        field_args.setdefault("label", "MAC Address")
        field_args["validators"].append(validators.MacAddress())
        return fields.StringField(**field_args)

    @converts(
        "sqlalchemy.dialects.postgresql.base.UUID",
        "UUID",
        "sqlalchemy_utils.types.uuid.UUIDType",
    )
    def conv_PGUuid(self, field_args, **extra):
        field_args.setdefault("label", "UUID")
        field_args["validators"].append(validators.UUID())
        field_args["filters"] = [
            avoid_empty_strings
        ]  # don't accept empty strings, or whitespace
        return fields.StringField(**field_args)

    @converts("sqlalchemy.sql.sqltypes.Uuid")
    def conv_SQLModelUuid(self, field_args, **extra):
        import uuid

        from wtforms import fields as wtf_fields

        class UUIDField(wtf_fields.StringField):
            def process_formdata(self, valuelist):
                if valuelist and valuelist[0]:
                    try:
                        # Convert string to UUID object
                        self.data = uuid.UUID(valuelist[0])  # type: ignore
                    except (ValueError, TypeError):
                        self.data = None
                        raise ValueError("Invalid UUID format") from None
                else:
                    self.data = None

            def process_data(self, value):
                # Handle data from model (could be UUID object or string)
                if value is not None:
                    try:
                        if isinstance(value, uuid.UUID):
                            self.data = value  # type: ignore
                        else:
                            # Convert string to UUID object
                            self.data = uuid.UUID(str(value))  # type: ignore
                    except (ValueError, TypeError):
                        self.data = None
                else:
                    self.data = None

            def process(self, formdata, data=None):
                # Override the main process method to ensure UUID conversion
                super().process(formdata, data)
                # After processing, ensure data is always a UUID object if not None
                if self.data is not None and not isinstance(self.data, uuid.UUID):
                    try:
                        self.data = uuid.UUID(str(self.data))  # type: ignore
                    except (ValueError, TypeError):
                        pass  # Keep original data if conversion fails

            def _value(self):
                # Convert UUID object to string for display
                if self.data:
                    return str(self.data)
                return ""

        field_args.setdefault("label", "UUID")
        field_args["validators"].append(validators.UUID())
        field_args["filters"] = [avoid_empty_strings]
        return UUIDField(**field_args)

    @converts(
        "sqlalchemy.dialects.postgresql.base.ARRAY", "sqlalchemy.sql.sqltypes.ARRAY"
    )
    def conv_ARRAY(self, field_args, **extra):
        return form.Select2TagsField(save_as_list=True, **field_args)

    @converts("HSTORE")
    def conv_HSTORE(self, field_args, **extra):
        inner_form = field_args.pop("form", HstoreForm)
        return InlineHstoreList(InlineFormField(inner_form), **field_args)

    @converts("JSON")
    def convert_JSON(self, field_args, **extra):
        return form.JSONField(**field_args)

    # Python native type converters for SQLModel
    @converts("str", "typing.Optional[str]", "str | None")
    def conv_python_str(self, column, field_args, **extra):
        self._string_common(column=column, field_args=field_args, **extra)
        return fields.StringField(**field_args)

    @converts("int", "typing.Optional[int]", "int | None")
    def conv_python_int(self, field_args, **extra):
        return fields.IntegerField(**field_args)

    @converts("float", "typing.Optional[float]", "float | None")
    def conv_python_float(self, field_args, **extra):
        field_args.setdefault("places", None)
        return fields.DecimalField(**field_args)

    @converts("bool", "typing.Optional[bool]", "bool | None")
    def conv_python_bool(self, field_args, **extra):
        return fields.BooleanField(**field_args)

    # Python enum converter for SQLModel
    def conv_python_enum(self, enum_class, column, field_args):
        """Convert Python enum types to Select2Field with proper choices."""
        # Generate choices from enum values
        available_choices = [
            (member.value, member.name.replace("_", " ").title())
            for member in enum_class
        ]
        accepted_values = [choice[0] for choice in available_choices]

        # Handle nullable fields
        if column is not None:
            if column.nullable:
                field_args["allow_blank"] = True
                accepted_values.append(None)
            self._nullable_common(column, field_args)

        field_args["choices"] = available_choices
        field_args["validators"].append(validators.AnyOf(accepted_values))

        # Coercion function: convert values to match choice keys
        def enum_coerce(value):
            if value is None or value == "":
                return None
            if isinstance(value, enum_class):
                # When form is populated from model,
                # num object → choice key (enum.value)
                return value.value
            # When form is submitted, string → choice key (should already be enum.value)
            return value

        field_args["coerce"] = enum_coerce
        return form.Select2Field(**field_args)

    # Pydantic type converters for SQLModel
    @converts("pydantic.EmailStr", "EmailStr", "pydantic.networks.EmailStr")
    def conv_pydantic_email(self, field_args, column=None, **extra):
        if column is not None:
            self._nullable_common(column, field_args)
        field_args["validators"].append(validators.Email())
        return fields.StringField(**field_args)

    @converts("pydantic.AnyUrl", "AnyUrl", "pydantic.HttpUrl", "HttpUrl")
    def conv_pydantic_url(self, field_args, column=None, **extra):
        if column is not None:
            self._nullable_common(column, field_args)
        field_args["validators"].append(validators.URL())
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    @converts("pydantic.SecretStr", "SecretStr")
    def conv_pydantic_secret(self, field_args, **extra):
        return fields.PasswordField(**field_args)

    @converts("pydantic.types.SecretBytes", "pydantic.SecretBytes", "SecretBytes")
    def conv_pydantic_secret_bytes(self, field_args, **extra):
        """Convert SecretBytes to password field for secure handling."""
        return fields.PasswordField(**field_args)

    @converts(
        "pydantic.networks.IPvAnyAddress",
        "pydantic.IPvAnyAddress",
        "IPvAnyAddress",
        "ipaddress.IPv4Address",
        "pydantic.IPv4Address",
        "IPv4Address",
        "ipaddress.IPv6Address",
        "pydantic.IPv6Address",
        "IPv6Address",
    )
    def conv_pydantic_ip_address(self, field_args, column=None, **extra):
        """Convert IP address types with proper validation."""
        if column is not None:
            self._nullable_common(column, field_args)
        field_args["validators"].append(validators.IPAddress())
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    @converts(
        "uuid.UUID",
        "UUID",
        "uuid.Annotated",
        "pydantic.UUID1",
        "UUID1",
        "pydantic.UUID3",
        "UUID3",
        "pydantic.UUID4",
        "UUID4",
        "pydantic.UUID5",
        "UUID5",
    )
    def conv_pydantic_uuid(self, field_args, column=None, **extra):
        """Convert UUID types with proper validation."""
        if column is not None:
            self._nullable_common(column, field_args)
        field_args["validators"].append(validators.UUID())
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    @converts("pydantic.types.Json", "pydantic.Json", "Json")
    def conv_pydantic_json(self, field_args, **extra):
        """Convert Pydantic Json type to JSONField."""
        return form.JSONField(**field_args)

    def conv_pydantic_constrained_field(
        self, model, field_info, type_annotation, field_args, **extra
    ):
        """Convert Pydantic constrained types with proper validation."""
        from flask_admin.contrib.sqlmodel.tools import get_pydantic_field_constraints
        from flask_admin.contrib.sqlmodel.tools import is_pydantic_constrained_type

        if not is_pydantic_constrained_type(type_annotation):
            return None

        constraints = get_pydantic_field_constraints(field_info, type_annotation)

        # Get the base type from the annotation
        from typing import get_args

        args = get_args(type_annotation)
        base_type = args[0] if args else str

        # Apply constraints as validators
        if base_type is str:
            # String field with length and pattern validation
            if "min_length" in constraints:
                field_args["validators"].append(
                    validators.Length(min=constraints["min_length"])
                )
            if "max_length" in constraints:
                field_args["validators"].append(
                    validators.Length(max=constraints["max_length"])
                )
            if "pattern" in constraints:
                field_args["validators"].append(
                    validators.Regexp(constraints["pattern"])
                )
            field_args["filters"] = [avoid_empty_strings]
            return fields.StringField(**field_args)

        elif base_type is int:
            # Integer field with range validation
            if "min_value" in constraints or "max_value" in constraints:
                min_val = constraints.get("min_value")
                max_val = constraints.get("max_value")
                field_args["validators"].append(
                    validators.NumberRange(min=min_val, max=max_val)
                )
            return fields.IntegerField(**field_args)

        elif base_type is float:
            # Decimal field with range validation
            if "min_value" in constraints or "max_value" in constraints:
                min_val = constraints.get("min_value")
                max_val = constraints.get("max_value")
                field_args["validators"].append(
                    validators.NumberRange(min=min_val, max=max_val)
                )
            field_args.setdefault("places", None)  # Allow any number of decimal places
            return fields.DecimalField(**field_args)

        # Fallback to regular field conversion
        return None

    @converts(
        "datetime.datetime",
        "typing.Optional[datetime.datetime]",
        "datetime.datetime | None",
    )
    def conv_python_datetime(self, field_args, **extra):
        return form.DateTimeField(**field_args)

    @converts("datetime.date", "typing.Optional[datetime.date]", "datetime.date | None")
    def conv_python_date(self, field_args, **extra):
        field_args.setdefault("widget", form.DatePickerWidget())
        return fields.DateField(**field_args)

    @converts("datetime.time", "typing.Optional[datetime.time]", "datetime.time | None")
    def conv_python_time(self, field_args, **extra):
        return form.TimeField(**field_args)


def avoid_empty_strings(value):
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


def choice_type_coerce_factory(type_):
    """
    Return a function to coerce a ChoiceType column, for use by Select2Field.
    :param type_: ChoiceType object
    """
    try:
        from sqlalchemy_utils import Choice

        choices = type_.choices
        if isinstance(choices, type) and issubclass(choices, Enum):
            key, choice_cls = "value", choices
        else:
            key, choice_cls = "code", Choice

        def choice_coerce(value):
            if value is None:
                return None
            if isinstance(value, choice_cls):
                return getattr(value, key)
            return type_.python_type(value)

        return choice_coerce
    except ImportError:
        # Fallback if sqlalchemy_utils not available
        def simple_coerce(value):
            return value

        return simple_coerce


def _resolve_prop(prop):
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
    model,
    converter,
    base_class=form.BaseForm,
    only=None,
    exclude=None,
    field_args=None,
    hidden_pk=False,
    ignore_hidden=True,
    extra_fields=None,
):
    """
    Generate form from the SQLModel.

    :param model:
        SQLModel to generate form from
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

    # Check if it's a SQLModel with table
    if issubclass(model, SQLModel):
        if not is_sqlmodel_table(model):
            raise TypeError("SQLModel must have table=True to generate forms")

        # SQLModel still uses SQLAlchemy's class manager under the hood
        if not hasattr(model, "_sa_class_manager"):
            raise TypeError("model must be a SQLModel mapped model")
    else:
        # Fallback for regular SQLAlchemy models
        if not hasattr(model, "_sa_class_manager"):
            raise TypeError("model must be a sqlalchemy mapped model")

    mapper = model._sa_class_manager.mapper  # type: ignore
    field_args = field_args or {}

    properties = list((p.key, p) for p in mapper.attrs)

    # For SQLModel, also include computed fields and properties with setters
    try:
        if issubclass(model, SQLModel):
            from .tools import get_wtform_compatible_fields

            # Get WTForms-compatible fields
            # (includes properties and computed fields with setters)
            wtform_compatible = get_wtform_compatible_fields(model)

            # Add WTForms-compatible properties
            # and computed fields that aren't already included
            for field in wtform_compatible:
                # Skip if field is already in properties (from mapper.attrs)
                if any(prop_name == field.name for prop_name, _ in properties):
                    continue

                # Add properties and computed fields with setters
                if field.is_property or field.is_computed:
                    if field.has_setter:
                        # Create a placeholder that will be handled by converter
                        properties.append((field.name, field))
    except (TypeError, AttributeError):
        # Fallback for mocks or non-SQLModel classes
        pass

        # Note: These will be handled in the convert method
        # using _convert_computed_field and _convert_property_field

    if only:

        def find(name):
            # If field is in extra_fields, it has higher priority
            if extra_fields and name in extra_fields:
                return name, FieldPlaceholder(extra_fields[name])

            # Check if it's a computed field in SQLModel (only for string names)
            if (
                isinstance(name, str)
                and issubclass(model, SQLModel)
                and is_computed_field(model, name)
            ):
                computed_fields = get_computed_fields(model)
                return name, computed_fields[name]

            # Check if it's a property with setter in SQLModel (only for string names)
            if isinstance(name, str):
                try:
                    if issubclass(model, SQLModel):
                        from .tools import get_wtform_compatible_fields

                        wtform_compatible = get_wtform_compatible_fields(model)
                        for field in wtform_compatible:
                            if (
                                field.name == name
                                and (field.is_property or field.is_computed)
                                and field.has_setter
                            ):
                                return name, field
                except (TypeError, AttributeError):
                    # Fallback for mocks or non-SQLModel classes
                    pass

            # Check if the field exists on the model before
            # trying to get it (only for string names)
            if isinstance(name, str) and not hasattr(model, name):
                raise ValueError(f"Field '{name}' not found on model {model.__name__}")

            column, path = get_field_with_path(
                model, name, return_remote_proxy_attr=False
            )

            if path and not (is_relationship(column) or is_association_proxy(column)):
                raise Exception(
                    "form column is located in another table and "
                    f"requires inline_models: {name}"
                )

            if is_association_proxy(column):
                return name, column

            # Handle Python properties directly (they don't have a key attribute)
            if isinstance(column, property):
                return name, column

            if hasattr(column, "key"):
                relation_name = column.key  # type: ignore

                if column is not None and hasattr(column, "property"):
                    return relation_name, column.property
                else:
                    return relation_name, column
            else:
                # Fallback for objects without key attribute
                return name, column

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
            model, mapper, name, prop, field_args.get(name), hidden_pk
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

    def __init__(self, session, view, model_converter):
        super().__init__(view)
        self.session = session
        self.model_converter = model_converter

    def get_info(self, p):
        # Already a subclass of InlineBaseFormAdmin or InlineFormAdmin
        if isinstance(p, self.form_admin_class):
            info = p
        # Tuple-style config: (Model, {options})
        elif isinstance(p, tuple):
            model, options = p
            info = self.form_admin_class(model, **options)
        # Raw model class (e.g. Address)
        elif isinstance(p, type) and issubclass(p, SQLModel):
            info = self.form_admin_class(p)
        else:
            # Attempt to unwrap a custom object with `model` attribute
            model = getattr(p, "model", None)
            if model is None or not issubclass(model, SQLModel):
                raise Exception(f"Unknown inline model admin: {repr(p)}")
            attrs = {
                attr: getattr(p, attr)
                for attr in dir(p)
                if not attr.startswith("_") and attr != "model"
            }
            info = self.form_admin_class(model, **attrs)

        # Always process AJAX references
        info._form_ajax_refs = self.process_ajax_refs(info)  # type: ignore

        return info

    def process_ajax_refs(self, info):
        refs = getattr(info, "form_ajax_refs", None)
        result = {}
        if refs:
            for name, opts in iteritems(refs):
                new_name = f"{info.model.__name__.lower()}-{name}"
                loader = (
                    create_ajax_loader(info.model, self.session, new_name, name, opts)
                    if isinstance(opts, dict)
                    else opts
                )
                loader.name = new_name
                result[name] = loader
                self.view._form_ajax_refs[new_name] = loader
        return result

    def _calculate_mapping_key_pair(
        self, parent_model: type[SQLModel], info: InlineFormAdmin
    ) -> dict[str, str]:
        result: dict[str, str] = {}

        parent_mapper = parent_model._sa_class_manager.mapper  # type: ignore
        child_mapper = info.model._sa_class_manager.mapper

        for rel in parent_mapper.relationships:
            if rel.mapper.class_ is info.model:
                # For self-referential models, only include
                # one-to-many relationships as inline
                # Skip many-to-one relationships in self-referential cases
                if parent_model is info.model and rel.direction.name == "MANYTOONE":
                    continue

                parent_side = rel.key

                # Find reverse relationship
                for back_rel in child_mapper.relationships:
                    if back_rel.mapper.class_ is parent_model:
                        child_side = back_rel.key
                        result[parent_side] = child_side
                        break
                else:
                    raise Exception(
                        f"Could not find reverse relationship from {info.model} to {parent_model}"  # noqa: E501
                    )

        if not result:
            raise Exception(
                f"No inline relationship found between {parent_model} and {info.model}"
            )

        return result

    def _find_back_populates(
        self,
        related_model: type[SQLModel],
        parent_model: type[SQLModel],
        forward_key: str,
    ) -> str:
        # Check regular fields
        for name, fld in related_model.model_fields.items():
            rel_type = fld.annotation
            if rel_type is parent_model or (
                hasattr(rel_type, "__origin__")
                and rel_type.__origin__ is list  # type: ignore
                and rel_type.__args__[0] is parent_model  # type: ignore
            ):
                return name

        # Check relationship fields in annotations
        for name, annotation in related_model.__annotations__.items():
            # Skip if already checked in model_fields
            if name in related_model.model_fields:
                continue

            rel_type = annotation
            # Handle Mapped[...] wrapper
            if hasattr(rel_type, "__origin__") and hasattr(rel_type, "__args__"):
                if len(rel_type.__args__) > 0:
                    inner_type = rel_type.__args__[0]
                    if inner_type is parent_model or (
                        hasattr(inner_type, "__origin__")
                        and inner_type.__origin__ is list
                        and len(inner_type.__args__) > 0
                        and inner_type.__args__[0] is parent_model
                    ):
                        return name

        # Fallback to default
        return parent_model.__name__.lower()

    def contribute(self, model, form_class, inline_model):
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
        info = self.get_info(inline_model)

        # Determine the forward and reverse key names based on field relationships
        forward_reverse_props_keys = self._calculate_mapping_key_pair(model, info)

        for forward_key, reverse_key in forward_reverse_props_keys.items():
            exclude = [reverse_key]
            if info.form_excluded_columns:  # type: ignore
                exclude.extend(info.form_excluded_columns)  # type: ignore

            # Create a new converter for the inline model
            converter = self.model_converter(self.session, info)

            # Get the form class for the inline model
            child_form = info.get_form()
            if child_form is None:
                child_form = get_form(
                    info.model,
                    converter,
                    base_class=info.form_base_class or form.BaseForm,  # type: ignore
                    only=info.form_columns,  # type: ignore
                    exclude=exclude,
                    field_args=info.form_args,  # type: ignore
                    hidden_pk=True,
                    extra_fields=info.form_extra_fields,  # type: ignore
                )

            # Allow further customization
            child_form = info.postprocess_form(child_form)

            # Set label and other field kwargs
            kwargs = {}
            label = self.get_label(info, forward_key)
            if label:
                kwargs["label"] = label

            if self.view.form_args:
                field_args = self.view.form_args.get(forward_key, {})
                kwargs.update(**field_args)

            # Contribute the field to the parent form
            setattr(
                form_class,
                forward_key,
                self.inline_field_list_type(
                    child_form,
                    self.session,
                    info.model,
                    reverse_key,
                    info,
                    **kwargs,
                ),
            )

        return form_class


class InlineOneToOneModelConverter(InlineModelConverter):
    inline_field_list_type = InlineModelOneToOneField  # type: ignore

    def _calculate_mapping_key_pair(self, model: type[SQLModel], info):
        forward_mapper = info.model._sa_class_manager.mapper
        target_mapper = model._sa_class_manager.mapper  # type: ignore

        for forward_prop in forward_mapper.relationships:
            if forward_prop.mapper.class_ == target_mapper.class_:
                back_populates = forward_prop.back_populates
                if not back_populates:
                    raise Exception(
                        f"Relationship '{forward_prop.key}' must define 'back_populates'"  # noqa: E501
                    )
                return {back_populates: forward_prop.key}

        raise Exception(f"No valid relationship found between {info.model} and {model}")

    def contribute(self, model: type[SQLModel], form_class, inline_model):
        info = self.get_info(inline_model)
        inline_relationships = self._calculate_mapping_key_pair(model, info)

        exclude = list(inline_relationships.values()) + list(
            info.form_excluded_columns or []  # type: ignore
        )  # type: ignore

        converter = self.model_converter(self.session, info)
        child_form = info.get_form()
        if child_form is None:
            child_form = get_form(
                info.model,
                converter,
                base_class=info.form_base_class or BaseForm,  # type: ignore
                only=info.form_columns,  # type: ignore
                exclude=exclude,
                field_args=info.form_args,  # type: ignore
                hidden_pk=True,
                extra_fields=info.form_extra_fields,  # type: ignore
            )

        child_form = info.postprocess_form(child_form)

        for field_name, fk_name in inline_relationships.items():
            setattr(
                form_class,
                field_name,
                self.inline_field_list_type(
                    child_form,
                    self.session,
                    info.model,
                    fk_name,
                    info,
                ),
            )

        return form_class
