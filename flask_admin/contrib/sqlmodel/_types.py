"""
Type definitions for SQLModel contrib module.

This module provides centralized type definitions for the SQLModel integration,
following the pattern established in flask_admin._types.
"""

import sys
import typing as t

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

if t.TYPE_CHECKING:
    # SQLModel imports
    from pydantic import BaseModel as T_PYDANTIC_MODEL
    from pydantic.fields import ComputedFieldInfo as T_PYDANTIC_COMPUTED_FIELD_INFO

    # Pydantic imports (optional)
    from pydantic.fields import FieldInfo as T_PYDANTIC_FIELD_INFO
    from sqlalchemy import Column as T_SQLALCHEMY_COLUMN
    from sqlalchemy.orm import InstrumentedAttribute as T_INSTRUMENTED_ATTRIBUTE
    from sqlalchemy.orm import Query as T_SQLALCHEMY_QUERY_ORM
    from sqlalchemy.orm import scoped_session as T_SCOPED_SESSION
    from sqlalchemy.sql.selectable import Select as T_SQLALCHEMY_SELECT
    from sqlmodel import Session as T_SQLMODEL_SESSION
    from sqlmodel import SQLModel as T_SQLMODEL

    # WTForms types
    from wtforms import Field as T_WTFORMS_FIELD
    from wtforms import SelectFieldBase as T_SELECT_FIELD_BASE
    from wtforms.form import BaseForm as T_BASE_FORM

    from flask_admin._types import T_FIELD_ARGS_VALIDATORS
    from flask_admin._types import T_ITER_CHOICES
    from flask_admin._types import T_OPTIONS
    from flask_admin._types import T_WIDGET_TYPE

    # Flask-Admin base types
    from flask_admin.model import BaseModelView as T_BASE_MODEL_VIEW
    from flask_admin.model.ajax import AjaxModelLoader as T_AJAX_MODEL_LOADER
    from flask_admin.model.filters import BaseFilter as T_BASE_FILTER

    # SQLModel-specific type unions
    T_SQLMODEL_QUERY = t.Union[T_SQLALCHEMY_QUERY_ORM, T_SQLALCHEMY_SELECT]
    T_SQLMODEL_SESSION_TYPE = t.Union[T_SQLMODEL_SESSION, T_SCOPED_SESSION]
    T_SQLMODEL_COLUMN = t.Union[str, T_SQLALCHEMY_COLUMN]
    T_SQLMODEL_FIELD_SOURCE = t.Union[
        T_PYDANTIC_FIELD_INFO,
        T_PYDANTIC_COMPUTED_FIELD_INFO,
        T_SQLALCHEMY_COLUMN,
        property,
    ]

else:
    # String type annotations for runtime
    T_SQLMODEL = "sqlmodel.SQLModel"
    T_SQLMODEL_SESSION = "sqlmodel.Session"
    T_SQLALCHEMY_QUERY_ORM = "sqlalchemy.orm.Query"
    T_SQLALCHEMY_SELECT = "sqlalchemy.sql.selectable.Select"
    T_SQLALCHEMY_COLUMN = "sqlalchemy.Column"
    T_INSTRUMENTED_ATTRIBUTE = "sqlalchemy.orm.InstrumentedAttribute"
    T_SCOPED_SESSION = "sqlalchemy.orm.scoped_session"

    T_PYDANTIC_FIELD_INFO = "pydantic.fields.FieldInfo"
    T_PYDANTIC_COMPUTED_FIELD_INFO = "pydantic.fields.ComputedFieldInfo"
    T_PYDANTIC_MODEL = "pydantic.BaseModel"

    T_BASE_MODEL_VIEW = "flask_admin.model.BaseModelView"
    T_BASE_FILTER = "flask_admin.model.filters.BaseFilter"
    T_AJAX_MODEL_LOADER = "flask_admin.model.ajax.AjaxModelLoader"
    T_FIELD_ARGS_VALIDATORS = "flask_admin._types.T_FIELD_ARGS_VALIDATORS"
    T_WIDGET_TYPE = "flask_admin._types.T_WIDGET_TYPE"
    T_OPTIONS = "flask_admin._types.T_OPTIONS"
    T_ITER_CHOICES = "flask_admin._types.T_ITER_CHOICES"

    T_WTFORMS_FIELD = "wtforms.Field"
    T_SELECT_FIELD_BASE = "wtforms.SelectFieldBase"
    T_BASE_FORM = "wtforms.form.BaseForm"

    T_SQLMODEL_QUERY = t.Union[T_SQLALCHEMY_QUERY_ORM, T_SQLALCHEMY_SELECT]
    T_SQLMODEL_SESSION_TYPE = t.Union[T_SQLMODEL_SESSION, T_SCOPED_SESSION]
    T_SQLMODEL_COLUMN = t.Union[str, T_SQLALCHEMY_COLUMN]
    T_SQLMODEL_FIELD_SOURCE = t.Union[
        T_PYDANTIC_FIELD_INFO,
        T_PYDANTIC_COMPUTED_FIELD_INFO,
        T_SQLALCHEMY_COLUMN,
        property,
    ]

# Common type aliases for SQLModel module
T_SQLMODEL_MODEL = T_SQLMODEL
T_SQLMODEL_FILTER = tuple[int, T_SQLMODEL_COLUMN, str]
T_SQLMODEL_COLUMN_LIST = t.Sequence[T_SQLMODEL_COLUMN]


# Field arguments specific to SQLModel
class T_SQLMODEL_FIELD_ARGS(t.TypedDict, total=False):
    """Type definition for SQLModel field arguments."""

    label: NotRequired[str]
    description: NotRequired[str]
    validators: NotRequired[list[t.Any]]
    filters: NotRequired[list[t.Callable[[t.Any], t.Any]]]
    widget: NotRequired[t.Any]
    render_kw: NotRequired[dict[str, t.Any]]
    default: NotRequired[t.Any]
    allow_blank: NotRequired[bool]
    choices: NotRequired[t.Any]
    coerce: NotRequired[t.Callable[[t.Any], t.Any]]
    query_factory: NotRequired[t.Callable[[], t.Any]]


# Ajax loader types for SQLModel
T_SQLMODEL_AJAX_LOADER = T_AJAX_MODEL_LOADER

# Form types
T_SQLMODEL_FORM = T_BASE_FORM

# View types
T_SQLMODEL_VIEW = T_BASE_MODEL_VIEW

# Widget types specific to SQLModel
T_SQLMODEL_WIDGET_TYPE = T_WIDGET_TYPE

# Filter types for SQLModel
T_SQLMODEL_BASE_FILTER = T_BASE_FILTER

# Primary key types
T_SQLMODEL_PK = t.Union[str, int, t.Any]
T_SQLMODEL_PK_TUPLE = tuple[t.Any, ...]
T_SQLMODEL_PK_VALUE = t.Union[T_SQLMODEL_PK, T_SQLMODEL_PK_TUPLE, None]

# ModelField type for our custom field representation
if t.TYPE_CHECKING:
    from flask_admin.contrib.sqlmodel.tools import ModelField as T_MODEL_FIELD
else:
    T_MODEL_FIELD = "flask_admin.contrib.sqlmodel.tools.ModelField"

# Type for model field lists
T_MODEL_FIELD_LIST = list[T_MODEL_FIELD]

# Type for field type mapping
T_FIELD_TYPE_MAP = dict[type, t.Callable[..., t.Any]]

# Type for choice tuples
T_CHOICE_TUPLE = tuple[t.Any, str]
T_CHOICE_LIST = list[T_CHOICE_TUPLE]

# Session execution result types
T_EXECUTION_RESULT = t.Any
T_SCALAR_RESULT = t.Any

# Query modifier types
T_QUERY_MODIFIER = t.Callable[[T_SQLMODEL_QUERY], T_SQLMODEL_QUERY]

# Property filter types for computed fields
T_PROPERTY_FILTER = tuple[property, str, t.Any]
T_PROPERTY_FILTER_LIST = list[T_PROPERTY_FILTER]

# Additional view-specific types
T_COLUMN_DICT = dict[T_SQLMODEL_COLUMN, T_SQLMODEL_COLUMN]
T_COLUMN_NAME_TUPLE = tuple[T_SQLMODEL_COLUMN, str]
T_COLUMN_NAME_LIST = list[T_COLUMN_NAME_TUPLE]
T_SEARCH_FIELD_TUPLE = tuple[t.Any, list[t.Any]]
T_SEARCH_FIELD_LIST = list[T_SEARCH_FIELD_TUPLE]

# Join-related types
T_JOIN_DICT = dict[str, list[t.Any]]

# Filter types for SQLModel views
T_FILTER_LIST = t.Optional[list[T_SQLMODEL_BASE_FILTER]]

# Model iterator types
T_MODEL_ITERATOR_ITEM = tuple[str, t.Any]
T_MODEL_ITERATOR = t.Iterator[T_MODEL_ITERATOR_ITEM]

# Type for get_list return value
T_GET_LIST_RESULT = tuple[t.Optional[int], t.Union[list[T_SQLMODEL], T_SQLMODEL_QUERY]]
