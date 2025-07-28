"""
SQLModel utility functions and helpers.

This module provides utility functions for working with SQLModel models,
including introspection, type handling, relationship resolution,
and compatibility helpers for bridging SQLModel and SQLAlchemy.
"""

import types
import typing as t
from dataclasses import dataclass
from typing import Any
from typing import get_args
from typing import get_origin
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from sqlalchemy import and_
from sqlalchemy import inspect
from sqlalchemy import or_
from sqlalchemy import tuple_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.clsregistry import _class_resolver

from flask_admin.contrib.sqlmodel._types import T_MODEL_FIELD_LIST

# Import centralized types
from flask_admin.contrib.sqlmodel._types import T_SQLMODEL_PK_VALUE

try:
    # SQLAlchemy 2.0
    from sqlalchemy.ext.associationproxy import AssociationProxyExtensionType

    ASSOCIATION_PROXY = AssociationProxyExtensionType.ASSOCIATION_PROXY
except ImportError:
    # Fallback for older versions
    from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.operators import eq  # type: ignore[attr-defined]

from flask_admin._compat import filter_list
from flask_admin._compat import string_types
from flask_admin.tools import escape  # noqa: F401
from flask_admin.tools import iterdecode  # noqa: F401
from flask_admin.tools import iterencode  # noqa: F401

# SQLModel imports
try:
    from pydantic.fields import ComputedFieldInfo
    from sqlmodel import SQLModel

    SQLMODEL_AVAILABLE = True
except ImportError:
    SQLModel = None  # type: ignore[misc,assignment]
    computed_field = None
    FieldInfo = None
    ComputedFieldInfo = None  # type: ignore[misc,assignment]
    SQLMODEL_AVAILABLE = False

# Special Pydantic types
try:
    from pydantic import AnyUrl
    from pydantic import EmailStr
    from pydantic import HttpUrl
    from pydantic import Json
    from pydantic import SecretBytes
    from pydantic import SecretStr

    PYDANTIC_TYPES_AVAILABLE = True
except ImportError:
    EmailStr = None  # type: ignore[misc,assignment]
    AnyUrl = None  # type: ignore[misc,assignment]
    HttpUrl = None  # type: ignore[misc,assignment]
    SecretStr = None  # type: ignore[misc,assignment]
    SecretBytes = None  # type: ignore[misc,assignment]
    Json = None  # type: ignore[misc]
    PYDANTIC_TYPES_AVAILABLE = False

# IP Address types
try:
    # IPv4Address and IPv6Address come from the standard library, not pydantic
    from ipaddress import IPv4Address
    from ipaddress import IPv6Address

    from pydantic import IPvAnyAddress

    PYDANTIC_IP_TYPES_AVAILABLE = True
except ImportError:
    IPvAnyAddress = None  # type: ignore[misc]
    IPv4Address = None  # type: ignore[misc,assignment]
    IPv6Address = None  # type: ignore[misc,assignment]
    PYDANTIC_IP_TYPES_AVAILABLE = False

# Constrained types (Pydantic v2)
try:
    from pydantic import confloat
    from pydantic import conint
    from pydantic import constr

    PYDANTIC_CONSTRAINED_TYPES_AVAILABLE = True
except ImportError:
    constr = None  # type: ignore[assignment]
    conint = None  # type: ignore[assignment]
    confloat = None  # type: ignore[assignment]
    PYDANTIC_CONSTRAINED_TYPES_AVAILABLE = False

# UUID types
try:
    from uuid import UUID

    from pydantic.types import UUID1
    from pydantic.types import UUID3
    from pydantic.types import UUID4
    from pydantic.types import UUID5

    PYDANTIC_UUID_TYPES_AVAILABLE = True
except ImportError:
    try:
        # Fallback to standard library UUID
        from uuid import UUID

        UUID1 = UUID3 = UUID4 = UUID5 = UUID
        PYDANTIC_UUID_TYPES_AVAILABLE = True
    except ImportError:
        UUID = UUID1 = UUID3 = UUID4 = UUID5 = None  # type: ignore[misc,assignment]
        PYDANTIC_UUID_TYPES_AVAILABLE = False

if TYPE_CHECKING:
    from pydantic.fields import ComputedFieldInfo


@dataclass
class ModelField:
    name: str
    type_: Any
    default: Any
    required: bool
    primary_key: bool
    description: Optional[str]
    source: Any  # the original Column, Pydantic Field, or computed field
    is_computed: bool = False
    is_property: bool = False
    has_setter: bool = False
    field_class: Optional[Any] = None  # Custom WTForms field class override


def _extract_field_class(field_info: Any) -> Optional[Any]:
    """
    Extract field_class from SQLModel Field definition.

    Checks for field_class in multiple locations:
    1. Direct field_class parameter
    2. json_schema_extra dictionary

    :param field_info: SQLModel FieldInfo object
    :return: WTForms field class or None
    """
    if field_info is None:
        return None

    # Check direct field_class parameter (primary method)
    if hasattr(field_info, "field_class"):
        field_class = getattr(field_info, "field_class", None)
        if field_class is not None:
            return field_class

    # Check json_schema_extra for field_class
    if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
        if isinstance(field_info.json_schema_extra, dict):
            field_class = field_info.json_schema_extra.get("field_class")
            if field_class is not None:
                return field_class

    return None


def parse_like_term(term: str) -> str:
    """Parse a search term for LIKE queries with special prefixes."""
    if term.startswith("^"):
        stmt = f"{term[1:]}%"
    elif term.startswith("="):
        stmt = term[1:]
    else:
        stmt = f"%{term}%"
    return stmt


def _get_python_type_info(type_annotation: Any) -> dict[str, Any]:
    """
    Extract information from Python type annotations including Optional, Union, etc.

    Returns:
        Dict with keys: 'base_type', 'is_optional', 'is_union', 'union_types'
    """
    origin = get_origin(type_annotation)
    args = get_args(type_annotation)

    info = {
        "base_type": type_annotation,
        "is_optional": False,
        "is_union": False,
        "union_types": [],
    }

    if origin is Union:
        info["is_union"] = True
        info["union_types"] = list(args)

        # Check if it's Optional (Union[T, None])
        if len(args) == 2 and type(None) in args:
            info["is_optional"] = True
            info["base_type"] = next(arg for arg in args if arg is not type(None))
        else:
            info["base_type"] = args[0]  # Use first type as base

    return info


def _is_special_pydantic_type(type_annotation: Any) -> bool:
    """Check if the type is a special Pydantic type like EmailStr, AnyUrl, etc."""
    type_info = _get_python_type_info(type_annotation)
    base_type = type_info["base_type"]

    # Check basic Pydantic types
    if PYDANTIC_TYPES_AVAILABLE:
        basic_types = [EmailStr, AnyUrl, HttpUrl, SecretStr, SecretBytes, Json]
        if all(t is not None for t in basic_types):
            if base_type in basic_types:
                return True

    # Check IP address types
    if PYDANTIC_IP_TYPES_AVAILABLE:
        ip_types = [IPvAnyAddress, IPv4Address, IPv6Address]
        if all(t is not None for t in ip_types):
            if base_type in ip_types:
                return True

    # Check UUID types
    if PYDANTIC_UUID_TYPES_AVAILABLE:
        uuid_types = [UUID, UUID1, UUID3, UUID4, UUID5]
        if all(t is not None for t in uuid_types):
            if base_type in uuid_types:
                return True

    return False


def is_pydantic_constrained_type(type_annotation: Any) -> bool:
    """Check if type is a Pydantic constrained type (Pydantic v2)."""
    if not PYDANTIC_CONSTRAINED_TYPES_AVAILABLE:
        return False

    # Pydantic v2 constrained types are typing.Annotated types
    origin = get_origin(type_annotation)
    if origin is not t.Annotated:
        return False

    args = get_args(type_annotation)
    if not args:
        return False

    # Check if any of the annotation args indicate constraints
    for arg in args[1:]:  # Skip the first arg which is the base type
        if arg is None:
            continue
        # Check for constraint objects (StringConstraints, Interval, etc.)
        if hasattr(arg, "__class__"):
            class_name = arg.__class__.__name__
            if any(
                constraint_type in class_name
                for constraint_type in ["Constraints", "Interval", "MultipleOf"]
            ):
                return True

    return False


def get_pydantic_field_constraints(
    field_info: Any, type_annotation: Any
) -> dict[str, Any]:
    """Extract Pydantic field constraints for WTForms validation."""
    constraints: dict[str, Any] = {}

    if not PYDANTIC_CONSTRAINED_TYPES_AVAILABLE:
        return constraints

    # Check if type is constrained
    if not is_pydantic_constrained_type(type_annotation):
        return constraints

    args = get_args(type_annotation)
    if not args:
        return constraints

    # Extract constraints from annotation args
    for arg in args[1:]:  # Skip the first arg which is the base type
        if arg is None:
            continue

        # StringConstraints
        if hasattr(arg, "__class__") and "StringConstraints" in arg.__class__.__name__:
            if hasattr(arg, "min_length") and arg.min_length is not None:
                constraints["min_length"] = arg.min_length
            if hasattr(arg, "max_length") and arg.max_length is not None:
                constraints["max_length"] = arg.max_length
            if hasattr(arg, "pattern") and arg.pattern is not None:
                constraints["pattern"] = arg.pattern

        # Interval constraints (for numeric types)
        elif hasattr(arg, "__class__") and "Interval" in arg.__class__.__name__:
            if hasattr(arg, "ge") and arg.ge is not None:
                constraints["min_value"] = arg.ge
            if hasattr(arg, "le") and arg.le is not None:
                constraints["max_value"] = arg.le
            if hasattr(arg, "gt") and arg.gt is not None:
                constraints["min_value"] = arg.gt + (
                    0.001 if isinstance(arg.gt, float) else 1
                )
            if hasattr(arg, "lt") and arg.lt is not None:
                constraints["max_value"] = arg.lt - (
                    0.001 if isinstance(arg.lt, float) else 1
                )

    return constraints


def _get_sqlmodel_property_info(model: Any, name: str) -> dict[str, Any]:
    """
    Get information about a SQLModel property or computed field.

    Returns:
        Dict with keys: 'is_property', 'is_computed', 'has_setter', 'type_', 'description'
    """  # noqa: E501
    info = {
        "is_property": False,
        "is_computed": False,
        "has_setter": False,
        "type_": None,
        "description": None,
    }

    if not hasattr(model, name):
        return info

    attr = getattr(model, name)

    # Check for @property decorator
    if isinstance(attr, property):
        info["is_property"] = True
        info["has_setter"] = attr.fset is not None

        # Try to get type from getter function annotations
        if hasattr(attr.fget, "__annotations__"):
            info["type_"] = attr.fget.__annotations__.get("return", None)

    # Check for @computed_field decorator (Pydantic v2)
    elif hasattr(attr, "__pydantic_computed_field__"):
        info["is_computed"] = True
        computed_info = attr.__pydantic_computed_field__

        if isinstance(computed_info, ComputedFieldInfo):
            info["type_"] = computed_info.return_type
            # Ensure description is always a string or None
            desc = computed_info.description
            info["description"] = str(desc) if desc is not None else None  # type: ignore[assignment]

        # Check if there's a setter method
        setter_name = f"set_{name}"
        if hasattr(model, setter_name):
            setter = getattr(model, setter_name)
            info["has_setter"] = callable(setter)

    # Check model_computed_fields for Pydantic computed fields
    elif (
        hasattr(model, "model_computed_fields") and name in model.model_computed_fields
    ):
        info["is_computed"] = True
        field_info = model.model_computed_fields[name]

        if hasattr(field_info, "return_type"):
            info["type_"] = field_info.return_type
        if hasattr(field_info, "description"):
            info["description"] = field_info.description

        # Check if there's a setter method
        setter_name = f"set_{name}"
        if hasattr(model, setter_name):
            setter = getattr(model, setter_name)
            info["has_setter"] = callable(setter)

    return info


def get_model_fields(model) -> T_MODEL_FIELD_LIST:
    """
    Get all fields from a model, supporting both SQLModel and SQLAlchemy.
    For SQLModel, includes regular fields, properties, and computed fields.
    """
    if not is_sqlmodel_class(model):
        # Traditional SQLAlchemy model
        if hasattr(model, "__table__"):
            fields = []
            for col in model.__table__.columns:
                fields.append(
                    ModelField(
                        name=col.name,
                        type_=col.type,
                        default=col.default.arg if col.default is not None else None,
                        required=not col.nullable and col.default is None,
                        primary_key=col.primary_key,
                        description=None,
                        source=col,
                        is_computed=False,
                        is_property=False,
                        has_setter=False,
                        field_class=None,  # SQLAlchemy columns don't have field class overrides  # noqa: E501
                    )
                )
            return fields
        else:
            return []

    # SQLModel handling
    fields = []

    # Get regular model fields
    if hasattr(model, "model_fields"):
        for name, field in model.model_fields.items():
            extra = (
                field.json_schema_extra or {}
                if hasattr(field, "json_schema_extra")
                else {}
            )

            # Get type information
            type_info = _get_python_type_info(field.annotation)

            # Check for primary key in various places
            is_primary_key = extra.get("primary_key", False)

            # Check if Field itself has primary_key attribute (handle PydanticUndefined)
            if not is_primary_key and hasattr(field, "primary_key"):
                pk_value = field.primary_key
                # Convert PydanticUndefined to False, True stays True
                is_primary_key = pk_value is True

            # Check if sa_column has primary_key=True
            if (
                not is_primary_key
                and hasattr(field, "sa_column")
                and field.sa_column is not None
            ):
                if hasattr(field.sa_column, "primary_key"):
                    is_primary_key = field.sa_column.primary_key

            fields.append(
                ModelField(
                    name=name,
                    type_=field.annotation,
                    default=field.default
                    if hasattr(field, "default") and field.default is not None
                    else None,
                    required=getattr(field, "is_required", lambda: False)()
                    if hasattr(field, "is_required")
                    else not type_info["is_optional"],
                    primary_key=is_primary_key,
                    description=extra.get("description")
                    or getattr(field, "description", None),
                    source=field,
                    is_computed=False,
                    is_property=False,
                    has_setter=False,
                    field_class=_extract_field_class(field),
                )
            )

    # Get computed fields
    if hasattr(model, "model_computed_fields"):
        for name, field_info in model.model_computed_fields.items():
            fields.append(
                ModelField(
                    name=name,
                    type_=getattr(field_info, "return_type", None),
                    default=None,
                    required=False,  # Computed fields are never required for input
                    primary_key=False,
                    description=getattr(field_info, "description", None),
                    source=field_info,
                    is_computed=True,
                    is_property=False,
                    has_setter=False,  # Will be updated below
                    field_class=None,  # Computed fields don't have custom field classes
                )
            )

    # Check for @property and @computed_field decorators on the class
    for name in dir(model):
        if name.startswith("_"):
            continue

        # Skip if already processed as a model field
        if any(f.name == name for f in fields):
            continue

        prop_info = _get_sqlmodel_property_info(model, name)

        if prop_info["is_property"] or prop_info["is_computed"]:
            fields.append(
                ModelField(
                    name=name,
                    type_=prop_info["type_"],
                    default=None,
                    required=False,  # Properties/computed fields are never required for input  # noqa: E501
                    primary_key=False,
                    description=prop_info["description"],
                    source=getattr(model, name),
                    is_computed=prop_info["is_computed"],
                    is_property=prop_info["is_property"],
                    has_setter=prop_info["has_setter"],
                    field_class=None,  # Properties don't have custom field classes
                )
            )

    # Update has_setter for computed fields (check for setter methods)
    for field in fields:
        if field.is_computed and not field.has_setter:
            setter_name = f"set_{field.name}"
            if hasattr(model, setter_name):
                setter = getattr(model, setter_name)
                field.has_setter = callable(setter)

    return fields


def get_wtform_compatible_fields(model) -> list[ModelField]:
    """
    Get fields that are compatible with WTForms.
    This includes regular fields and properties/computed fields with setters.
    """
    all_fields = get_model_fields(model)

    wtform_fields = []
    for field in all_fields:
        # Include regular fields
        if not field.is_computed and not field.is_property:
            wtform_fields.append(field)
        # Include properties/computed fields with setters
        elif field.has_setter:
            wtform_fields.append(field)

    return wtform_fields


def get_readonly_fields(model) -> list[ModelField]:
    """
    Get fields that are read-only (computed fields and properties without setters).
    """
    all_fields = get_model_fields(model)

    readonly_fields = []
    for field in all_fields:
        if (field.is_computed or field.is_property) and not field.has_setter:
            readonly_fields.append(field)

    return readonly_fields


def filter_foreign_columns(base_table, columns):
    """
    Return list of columns that belong to passed table.

    :param base_table: Table to check against
    :param columns: List of columns to filter
    """
    return filter_list(lambda c: c.table == base_table, columns)


def is_sqlmodel_class(model: Any) -> bool:
    """Check if a model is a SQLModel class."""
    if not SQLMODEL_AVAILABLE:
        return False
    return isinstance(model, type) and issubclass(model, SQLModel)


def get_primary_key(model: Any) -> T_SQLMODEL_PK_VALUE:
    """
    Return primary key name from a model. If the primary key consists of multiple
    columns, return the corresponding ``tuple``.

    Works with both SQLModel and SQLAlchemy models.

    :param model: Model class
    """
    # For SQLModel, we can use the model's metadata
    if is_sqlmodel_class(model):
        fields = get_model_fields(model)
        pks = [field.name for field in fields if field.primary_key]
    else:
        # Traditional SQLAlchemy model
        if hasattr(model, "_sa_class_manager"):
            mapper = model._sa_class_manager.mapper
            pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]
        else:
            # Direct SQLAlchemy inspection
            mapper = inspect(model)
            pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]

    if len(pks) == 1:
        return pks[0]
    elif len(pks) > 1:
        return tuple(pks)
    else:
        return None


def has_multiple_pks(model: Any) -> bool:
    """
    Return True, if the model has more than one primary key.
    Works with both SQLModel and SQLAlchemy models.
    """
    if is_sqlmodel_class(model):
        fields = get_model_fields(model)
        pk_count = sum(1 for field in fields if field.primary_key)
        return pk_count > 1
    else:
        # Traditional SQLAlchemy model
        if hasattr(model, "_sa_class_manager"):
            return len(model._sa_class_manager.mapper.primary_key) > 1
        else:
            mapper = inspect(model)
            return len(mapper.primary_key) > 1


def get_primary_key_types(model: Any) -> dict[str, Any]:
    """
    Get primary key field names and their Python types.

    :param model: SQLModel or SQLAlchemy model class
    :return: Dictionary mapping primary key names to their Python types
    """
    pk_types = {}

    if is_sqlmodel_class(model):
        fields = get_model_fields(model)
        for field in fields:
            if field.primary_key:
                type_info = _get_python_type_info(field.type_)
                pk_types[field.name] = type_info["base_type"]
    else:
        # Traditional SQLAlchemy model
        mapper = inspect(model)
        for col in mapper.primary_key:
            prop = mapper.get_property_by_column(col)
            pk_types[prop.key] = col.type.python_type

    return pk_types


def convert_pk_value(value: str, pk_type: Any) -> Any:
    """
    Convert a string primary key value to its proper Python type.

    :param value: String value from URL parameter
    :param pk_type: Python type to convert to
    :return: Converted value
    """
    if value is None or value == "":
        return None

    # Already correct type
    if isinstance(value, pk_type):
        return value

    # String type - return as-is
    if pk_type is str:
        return value

    # Integer types
    if pk_type is int:
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to integer") from None

    # Float types
    if pk_type is float:
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to float") from None

    # UUID types
    if PYDANTIC_UUID_TYPES_AVAILABLE and pk_type in [UUID, UUID1, UUID3, UUID4, UUID5]:
        try:
            import uuid

            return uuid.UUID(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to UUID") from None

    # Boolean types
    if pk_type is bool:
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean")

    # For other types, try direct conversion
    try:
        return pk_type(value)
    except (ValueError, TypeError):
        # If all else fails, return the string value
        # This allows SQLAlchemy to attempt its own conversion
        return value


def convert_pk_from_url(model: Any, pk_value: Any) -> Any:
    """
    Convert primary key value(s) from URL parameters to proper Python types.

    This function handles both single and composite primary keys, converting
    string values from URL parameters to the appropriate Python types expected
    by the model's primary key fields.

    :param model: SQLModel or SQLAlchemy model class
    :param pk_value: Primary key value from URL (string or iterdecode result)
    :return: Converted primary key value(s)
    """
    pk_types = get_primary_key_types(model)
    pk_names = get_primary_key(model)
    is_composite_pk = isinstance(pk_names, tuple)

    # Handle tuple from iterdecode
    if isinstance(pk_value, tuple):
        if is_composite_pk:
            # Model has composite PK, convert each part
            assert isinstance(pk_names, tuple)  # Help mypy understand pk_names is tuple
            if len(pk_value) != len(pk_names):
                raise ValueError(
                    f"Primary key value count ({len(pk_value)}) doesn't match model ({len(pk_names)})"  # noqa: E501
                )

            converted_values = []
            for name, value in zip(pk_names, pk_value):
                pk_type = pk_types.get(str(name), str)
                converted_values.append(convert_pk_value(value, pk_type))

            return tuple(converted_values)
        else:
            # Model has single PK but got tuple (from iterdecode)
            if len(pk_value) == 1:
                # Single value tuple - unwrap and convert
                pk_type = pk_types.get(str(pk_names), str) if pk_names else str
                return convert_pk_value(pk_value[0], pk_type)
            elif len(pk_value) == 0:
                # Empty tuple
                return None
            else:
                # Multiple values for single PK
                raise ValueError(
                    f"Model has single primary key '{pk_names}' but got multiple values: {pk_value}"  # noqa: E501
                )

    # Handle single value (not from iterdecode)
    else:
        if is_composite_pk:
            # Model has composite PK but got single value
            raise ValueError(
                f"Model has composite primary key {pk_names} but got single value"
            )
        else:
            # Model has single PK, convert the value
            pk_type = pk_types.get(str(pk_names), str) if pk_names else str
            return convert_pk_value(pk_value, pk_type)

    # Fallback - return original value
    return pk_value


def tuple_operator_in(model_pk: list[Any], ids: list[tuple[Any, ...]]) -> Optional[Any]:
    """
    The ``tuple_`` Operator only works on certain engines like MySQL or Postgresql. It
    does not work with sqlite.

    The function returns an ``or_`` - operator, that contains ``and_`` - operators
    for every single ``tuple`` in ``ids``.

    Example::

      model_pk =  [ColumnA, ColumnB]
      ids = ((1,2), (1,3))

      tuple_operator_in(model_pk, ids)
      ->
      or_( and_( ColumnA == 1, ColumnB == 2), and_( ColumnA == 1, ColumnB == 3) )

    The returning operator can be used within a ``filter()``, as it is
    just an ``or_`` operator
    """
    ands = []
    for id_tuple in ids:
        k = []
        for i in range(len(model_pk)):
            k.append(eq(model_pk[i], id_tuple[i]))
        ands.append(and_(*k))
    if len(ands) >= 1:
        return or_(*ands)
    else:
        return None


def get_query_for_ids(modelquery, model: Any, ids: list[Any]):
    """
    Return a query object filtered by primary key values passed in `ids` argument.

    Unfortunately, it is not possible to use `in_` filter if model has more than one
    primary key.

    Works with both SQLModel and SQLAlchemy models.
    """
    if has_multiple_pks(model):
        # Decode keys to tuples and convert to proper types
        decoded_ids = [iterdecode(v) for v in ids]
        converted_ids = [
            convert_pk_from_url(model, decoded_pk) for decoded_pk in decoded_ids
        ]

        # Get model primary key property references
        pk_names = get_primary_key(model)
        if isinstance(pk_names, tuple):
            model_pk = [getattr(model, str(name)) for name in pk_names]
        else:
            model_pk = [getattr(model, str(pk_names))]

        try:
            query = modelquery.filter(tuple_(*model_pk).in_(converted_ids))
            # Only the execution of the query will tell us, if the ``tuple_``
            # operator really works
            query.all()
        except DBAPIError:
            query = modelquery.filter(tuple_operator_in(model_pk, converted_ids))
    else:
        # Convert single primary key values to proper types
        pk_name = get_primary_key(model)
        pk_types = get_primary_key_types(model)
        pk_type = pk_types.get(str(pk_name), str) if pk_name else str

        converted_ids = [convert_pk_value(id_val, pk_type) for id_val in ids]

        model_pk = getattr(model, str(pk_name))
        query = modelquery.filter(model_pk.in_(converted_ids))

    return query


def get_columns_for_field(field):
    """Get columns for a field, handling both SQLModel and SQLAlchemy fields."""
    if (
        not field
        or not hasattr(field, "property")
        or not hasattr(field.property, "columns")
        or not field.property.columns
    ):
        raise Exception(f"Invalid field {field}: does not contains any columns.")

    return field.property.columns


def need_join(model: Any, table) -> bool:
    """
    Check if join to a table is necessary.
    Works with both SQLModel and SQLAlchemy models.
    """
    if is_sqlmodel_class(model) and hasattr(model, "__table__"):
        # SQLModel with table=True
        mapper = inspect(model)
        return table not in mapper.tables
    elif hasattr(model, "_sa_class_manager"):
        # Traditional SQLAlchemy
        return table not in model._sa_class_manager.mapper.tables
    else:
        # Fallback to inspection
        mapper = inspect(model)
        return table not in mapper.tables


def get_field_with_path(
    model: Any, name: Union[str, Any], return_remote_proxy_attr: bool = True
):
    """
    Resolve property by name and figure out its join path.

    Join path might contain both properties and tables.
    Works with both SQLModel and SQLAlchemy models.
    """
    path = []

    # For strings, resolve path
    if isinstance(name, string_types):
        # create a copy to keep original model as `model`
        current_model = model

        value = None
        for attribute in name.split("."):
            value = getattr(current_model, attribute)

            if is_association_proxy(value):
                relation_values = value.attr
                if return_remote_proxy_attr:
                    value = value.remote_attr
            else:
                relation_values = [value]

            for relation_value in relation_values:
                if is_relationship(relation_value):
                    current_model = relation_value.property.mapper.class_
                    table = current_model.__table__
                    if need_join(model, table):
                        path.append(relation_value)

        attr = value
    else:
        attr = name

        # Determine joins if table.column (relation object) is provided
        if isinstance(attr, InstrumentedAttribute) or is_association_proxy(attr):
            columns = get_columns_for_field(attr)

            if len(columns) > 1:
                raise Exception(f"Can only handle one column for {name}")

            column = columns[0]

            # TODO: Use SQLAlchemy "path-finder" to find exact join path to the
            #  target property
            if need_join(model, column.table):
                path.append(column.table)

    return attr, path


# copied from sqlalchemy-utils
def get_hybrid_properties(model: Any) -> dict:
    """
    Get hybrid properties from a model.
    Works with both SQLModel and SQLAlchemy models.
    """
    return dict(
        (key, prop)
        for key, prop in inspect(model).all_orm_descriptors.items()
        if isinstance(prop, hybrid_property)
    )


def is_hybrid_property(model: Any, attr_name: Union[str, Any]) -> bool:
    """
    Check if an attribute is a hybrid property.
    Works with both SQLModel and SQLAlchemy models.
    """
    if isinstance(attr_name, string_types):
        names = attr_name.split(".")
        last_model = model
        for i in range(len(names) - 1):
            attr = getattr(last_model, names[i])
            if is_association_proxy(attr):
                attr = attr.remote_attr
            last_model = attr.property.argument
            if isinstance(last_model, string_types):
                last_model = attr.property._clsregistry_resolve_name(last_model)()
            elif isinstance(last_model, _class_resolver):
                # Handle both SQLModel and SQLAlchemy registry
                if hasattr(model, "_decl_class_registry"):
                    last_model = model._decl_class_registry[last_model.arg]
                elif hasattr(model, "registry") and hasattr(
                    model.registry, "_class_registry"
                ):
                    last_model = model.registry._class_registry[last_model.arg]
                else:
                    # Fallback for SQLModel
                    last_model = last_model.arg
            elif isinstance(last_model, (types.FunctionType, types.MethodType)):
                last_model = last_model()
        last_name = names[-1]
        return last_name in get_hybrid_properties(last_model)
    else:
        return attr_name.name in get_hybrid_properties(model)


def get_computed_fields(model):
    """
    Get computed fields from SQLModel.
    SQLModel uses Pydantic's computed_field instead of SQLAlchemy's hybrid_property.
    """
    if not is_sqlmodel_class(model):
        raise TypeError("model must be a SQLModel class")

    computed_fields = {}

    # Get from model_computed_fields (Pydantic v2)
    if hasattr(model, "model_computed_fields"):
        computed_fields.update(model.model_computed_fields)

    # Also check for methods decorated with @computed_field
    for name in dir(model):
        if name.startswith("_"):
            continue
        attr = getattr(model, name)
        if hasattr(attr, "__pydantic_computed_field__"):
            computed_fields[name] = attr

    return computed_fields


def get_sqlmodel_properties(model) -> dict[str, property]:
    """
    Get all @property decorated methods from a SQLModel class.
    """
    if not is_sqlmodel_class(model):
        raise TypeError("model must be a SQLModel class")

    properties = {}
    for name in dir(model):
        if name.startswith("_"):
            continue
        attr = getattr(model, name)
        if isinstance(attr, property):
            properties[name] = attr

    return properties


def is_computed_field(model, attr_name):
    """
    Check if attribute is a computed field in SQLModel.
    This is the SQLModel equivalent of is_hybrid_property.
    """
    if not is_sqlmodel_class(model):
        return False

    if isinstance(attr_name, string_types):
        names = attr_name.split(".")
        last_model = model
        for i in range(len(names) - 1):
            attr = getattr(last_model, names[i])
            if is_association_proxy(attr):
                attr = attr.remote_attr
            last_model = attr.property.argument
            if isinstance(last_model, string_types):
                last_model = attr.property._clsregistry_resolve_name(last_model)()
            elif isinstance(last_model, _class_resolver):
                if hasattr(model, "_decl_class_registry"):
                    last_model = model._decl_class_registry[last_model.arg]
                elif hasattr(model, "registry") and hasattr(
                    model.registry, "_class_registry"
                ):
                    last_model = model.registry._class_registry[last_model.arg]
                else:
                    last_model = last_model.arg
            elif isinstance(last_model, (types.FunctionType, types.MethodType)):
                last_model = last_model()
        last_name = names[-1]
        return last_name in get_computed_fields(last_model)
    else:
        return attr_name.name in get_computed_fields(model)


def is_sqlmodel_property(model, attr_name):
    """
    Check if attribute is a @property in SQLModel.
    """
    if not is_sqlmodel_class(model):
        return False

    if isinstance(attr_name, string_types):
        names = attr_name.split(".")
        last_model = model
        for i in range(len(names) - 1):
            attr = getattr(last_model, names[i])
            if is_association_proxy(attr):
                attr = attr.remote_attr
            last_model = attr.property.argument
            if isinstance(last_model, string_types):
                last_model = attr.property._clsregistry_resolve_name(last_model)()
            elif isinstance(last_model, _class_resolver):
                if hasattr(model, "_decl_class_registry"):
                    last_model = model._decl_class_registry[last_model.arg]
                elif hasattr(model, "registry") and hasattr(
                    model.registry, "_class_registry"
                ):
                    last_model = model.registry._class_registry[last_model.arg]
                else:
                    last_model = last_model.arg
            elif isinstance(last_model, (types.FunctionType, types.MethodType)):
                last_model = last_model()
        last_name = names[-1]
        return last_name in get_sqlmodel_properties(last_model)
    else:
        return isinstance(getattr(model, attr_name.name, None), property)


def is_relationship(attr) -> bool:
    """Check if an attribute is a relationship."""
    return hasattr(attr, "property") and hasattr(attr.property, "direction")


def is_association_proxy(attr) -> bool:
    """Check if an attribute is an association proxy."""
    if hasattr(attr, "parent"):
        attr = attr.parent
    return hasattr(attr, "extension_type") and attr.extension_type == ASSOCIATION_PROXY


def get_model_table(model: Any):
    """
    Get the table from a model, handling both SQLModel and SQLAlchemy.

    :param model: SQLModel or SQLAlchemy model class
    :return: The table object
    """
    if is_sqlmodel_class(model):
        if hasattr(model, "__table__"):
            return model.__table__
        else:
            # SQLModel without table=True doesn't have a table
            return None
    else:
        # Traditional SQLAlchemy
        return getattr(model, "__table__", None)


def is_sqlmodel_table_model(model: Any) -> bool:
    """
    Check if model is a SQLModel with table=True.

    :param model: Model to check
    :return: True if it's a SQLModel with table=True
    """
    return (
        is_sqlmodel_class(model)
        and hasattr(model, "__table__")
        and model.__table__ is not None
    )


# Alias for backward compatibility and cleaner naming
def is_sqlmodel_table(model: Any) -> bool:
    """
    Check if the model is a SQLModel table (has table=True).
    Alias for is_sqlmodel_table_model() for cleaner naming.
    """
    return is_sqlmodel_table_model(model)


def get_sqlmodel_fields(model: Any) -> dict:
    """
    Get all fields from a SQLModel, including both regular fields and computed fields.

    :param model: SQLModel class
    :return: Dictionary of field names and field objects
    """
    if not SQLMODEL_AVAILABLE:
        raise ImportError("SQLModel is not available")

    if not is_sqlmodel_class(model):
        raise TypeError("model must be a SQLModel class")

    fields = {}

    # Get regular fields
    if hasattr(model, "model_fields"):
        fields.update(model.model_fields)

    # Get computed fields if available
    computed_fields = get_computed_fields(model)
    fields.update(computed_fields)

    return fields


def get_sqlmodel_column_names(model: Any) -> list[str]:
    """
    Get column names from SQLModel table.

    :param model: SQLModel class with table=True
    :return: List of column names
    """
    if not is_sqlmodel_table(model):
        raise TypeError("model must be a SQLModel table (with table=True)")

    return [column.name for column in model.__table__.columns]


def get_sqlmodel_field_names(model: Any) -> list[str]:
    """
    Get field names from a SQLModel class (works for both table and non-table models).

    :param model: SQLModel class
    :return: List of field names
    """
    if not is_sqlmodel_class(model):
        raise TypeError("model must be a SQLModel class")

    fields = get_sqlmodel_fields(model)
    return list(fields.keys())


def get_all_model_fields(model: Any) -> dict:
    """
    Universal function to get all fields from any model type.
    Works with SQLModel (table and non-table) and SQLAlchemy models.

    :param model: Model class (SQLModel or SQLAlchemy)
    :return: Dictionary of field information
    """
    if is_sqlmodel_class(model):
        return get_sqlmodel_fields(model)
    else:
        # For SQLAlchemy models, use inspection
        mapper = inspect(model)
        fields = {}

        # Get column properties
        for prop in mapper.iterate_properties():
            if hasattr(prop, "columns"):
                fields[prop.key] = prop

        return fields


def resolve_model(obj: object, model_name: Union[str, None] = None) -> Any:
    """
    Resolve and return the actual ORM model from a SQLAlchemy Row or return the object as-is
    if it's already an ORM model.

    If the row contains multiple models (e.g. from a JOIN), you must specify `model_name`.
    """  # noqa: E501
    if hasattr(obj, "__table__"):  # It's already a SQLModel ORM instance
        return obj

    # Try to handle SQLAlchemy Row or RowMapping
    mapping = getattr(obj, "_mapping", None)
    if mapping is None:
        raise TypeError(f"Object of type {type(obj)} is not a Row or ORM model.")

    keys = list(mapping.keys())

    # If the user provides a model name (e.g., 'User'), extract that specifically
    if model_name:
        if model_name not in mapping:
            raise ValueError(f"Model name '{model_name}' not found. Available: {keys}")
        resolved = mapping[model_name]
    elif len(keys) == 1:
        # Only one key → assume this is the ORM model
        resolved = mapping[keys[0]]
    else:
        raise ValueError(
            f"Row contains multiple models: {keys}. "
            f"Pass `model_name='YourModelName'` to resolve the correct one."
        )

    if hasattr(resolved, "__table__"):
        return resolved
    else:
        raise TypeError(
            f"Resolved object is not a valid SQLModel ORM instance: {type(resolved)}"
        )


# Additional utility functions for WTForms integration


def create_property_setter(model_class: Any, field_name: str, field_type: Any = None):
    """
    Create a setter method for a computed field or property to make it WTForms compatible.

    This is a utility function that can be used to dynamically add setters to computed fields
    or properties that don't have them, enabling WTForms compatibility.

    :param model_class: SQLModel class
    :param field_name: Name of the field to create setter for
    :param field_type: Optional type for validation
    :return: Setter function
    """  # noqa: E501

    def setter_method(self, value):
        # Store the value in a private attribute
        private_attr = f"_wtf_{field_name}"
        setattr(self, private_attr, value)

    setter_method.__name__ = f"set_{field_name}"
    setter_method.__doc__ = f"Setter for {field_name} field (WTForms compatibility)"

    return setter_method


def make_computed_field_wtforms_compatible(model_class: Any, field_name: str):
    """
    Add a setter method to a computed field to make it WTForms compatible.

    This function dynamically adds a setter method to the model class.

    :param model_class: SQLModel class
    :param field_name: Name of the computed field
    """
    if not is_sqlmodel_class(model_class):
        raise TypeError("model_class must be a SQLModel class")

    setter_name = f"set_{field_name}"
    if not hasattr(model_class, setter_name):
        setter_method = create_property_setter(model_class, field_name)
        setattr(model_class, setter_name, setter_method)


def get_field_value_with_fallback(instance: Any, field_name: str, default=None):
    """
    Get field value with fallback to private WTForms storage.

    This is useful for getting values from computed fields that have been
    set through WTForms but not yet processed.

    :param instance: Model instance
    :param field_name: Field name
    :param default: Default value if not found
    :return: Field value
    """
    # Try to get the actual field value
    if hasattr(instance, field_name):
        try:
            return getattr(instance, field_name)
        except (AttributeError, Exception):
            pass

    # Fallback to private WTForms storage
    private_attr = f"_wtf_{field_name}"
    if hasattr(instance, private_attr):
        return getattr(instance, private_attr)

    return default


def set_field_value_with_fallback(instance: Any, field_name: str, value):
    """
    Set field value with fallback to private WTForms storage.

    This tries to use a setter method first, then falls back to direct assignment
    or private storage.

    :param instance: Model instance
    :param field_name: Field name
    :param value: Value to set
    """
    # Try to use setter method first
    setter_name = f"set_{field_name}"
    if hasattr(instance, setter_name):
        setter = getattr(instance, setter_name)
        if callable(setter):
            setter(value)
            return

    # Try direct assignment
    if hasattr(instance, field_name):
        try:
            setattr(instance, field_name, value)
            return
        except (AttributeError, Exception):
            pass

    # Fallback to private storage
    private_attr = f"_wtf_{field_name}"
    setattr(instance, private_attr, value)


def get_field_python_type(field: ModelField) -> Any:
    """
    Get the Python type for a field, handling Optional, Union, and special Pydantic types.

    :param field: ModelField instance
    :return: Python type or ``tuple`` of types for Union
    """  # noqa: E501
    if field.type_ is None:
        return str  # Default fallback

    type_info = _get_python_type_info(field.type_)

    # Handle special Pydantic types
    if _is_special_pydantic_type(field.type_):
        return str  # Most special types are string-based

    # Handle Union types
    if type_info["is_union"] and not type_info["is_optional"]:
        return type_info["union_types"]

    return type_info["base_type"]


def is_field_optional(field: ModelField) -> bool:
    """
    Check if a field is optional (can be None).

    :param field: ModelField instance
    :return: True if field is optional
    """
    if field.type_ is None:
        return True

    type_info = _get_python_type_info(field.type_)
    return type_info["is_optional"] or not field.required


def get_field_constraints(field: ModelField) -> dict[str, Any]:
    """
    Extract constraints from a field for validation.

    This is a placeholder for future constraint extraction functionality.

    :param field: ModelField instance
    :return: Dictionary of constraints
    """
    constraints = {}

    if hasattr(field.source, "constraints"):
        # This would handle Pydantic Field constraints
        constraints.update(field.source.constraints)

    # Add more constraint extraction logic as needed
    return constraints


def validate_field_type(value: Any, field: ModelField) -> tuple[bool, str]:
    """
    Validate a value against a field's type constraints.

    This is a basic type validation function that can be extended.

    :param value: Value to validate
    :param field: ModelField instance
    :return: ``Tuple`` of (is_valid, error_message)
    """
    if value is None:
        if field.required:
            return False, f"Field '{field.name}' is required"
        return True, ""

    python_type = get_field_python_type(field)

    # Handle Union types
    if isinstance(python_type, (list, tuple)):
        if not any(isinstance(value, t) for t in python_type):
            type_names = [t.__name__ for t in python_type]
            return (
                False,
                f"Field '{field.name}' must be one of: {', '.join(type_names)}",
            )
    else:
        # Single type validation
        if not isinstance(value, python_type):
            return False, f"Field '{field.name}' must be of type {python_type.__name__}"

    return True, ""


# Helper functions for debugging and introspection


def debug_model_fields(model: Any) -> str:
    """
    Generate a debug string showing all fields and their properties.

    :param model: SQLModel or SQLAlchemy model class
    :return: Debug string
    """
    fields = get_model_fields(model)

    debug_lines = [f"Model: {model.__name__}"]
    debug_lines.append(f"Is SQLModel: {is_sqlmodel_class(model)}")
    debug_lines.append(f"Has table: {hasattr(model, '__table__')}")
    debug_lines.append("Fields:")

    for field in fields:
        field_info = []
        field_info.append(f"  {field.name}: {field.type_}")

        if field.required:
            field_info.append("required")
        if field.primary_key:
            field_info.append("primary_key")
        if field.is_computed:
            field_info.append("computed")
        if field.is_property:
            field_info.append("property")
        if field.has_setter:
            field_info.append("has_setter")
        if field.default is not None:
            field_info.append(f"default={field.default}")
        if field.description:
            field_info.append(f"desc='{field.description}'")

        debug_lines.append(" | ".join(field_info))

    return "\n".join(debug_lines)


def get_model_field_summary(model: Any) -> dict[str, dict[str, Any]]:
    """
    Get a summary of all fields in a model.

    :param model: SQLModel or SQLAlchemy model class
    :return: Dictionary with field summaries
    """
    fields = get_model_fields(model)

    summary = {}
    for field in fields:
        summary[field.name] = {
            "type": field.type_,
            "required": field.required,
            "primary_key": field.primary_key,
            "is_computed": field.is_computed,
            "is_property": field.is_property,
            "has_setter": field.has_setter,
            "default": field.default,
            "description": field.description,
            "wtforms_compatible": not (field.is_computed or field.is_property)
            or field.has_setter,
            "readonly": (field.is_computed or field.is_property)
            and not field.has_setter,
        }

    return summary
