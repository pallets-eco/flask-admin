import sys
import typing as t
from enum import Enum
from os import PathLike

import wtforms.widgets
from flask import Response
from jinja2.runtime import Context
from markupsafe import Markup
from werkzeug.wrappers import Response as Wkzg_Response
from wtforms import Field
from wtforms.form import BaseForm
from wtforms.utils import UnsetValue
from wtforms.widgets import Input

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

if t.TYPE_CHECKING:
    from flask_admin.base import BaseView as T_VIEW  # noqa
    from flask_admin.contrib.sqla.validators import InputRequired as T_INPUT_REQUIRED
    from flask_admin.contrib.sqla.validators import (
        TimeZoneValidator as T_TIMEZONE_VALIDATOR,
    )
    from flask_admin.contrib.sqla.validators import Unique as T_UNIQUE
    from flask_admin.form import FormOpts as T_FORM_OPTS  # noqa
    from flask_admin.form.rules import (
        FieldSet as T_FIELD_SET,
        BaseRule as T_BASE_RULE,
        Header as T_HEADER,
        Field as T_FLASK_ADMIN_FIELD,
        Macro as T_MACRO,
    )
    from flask_admin.model import BaseModelView as T_MODEL_VIEW
    from flask_admin.model.ajax import AjaxModelLoader as T_AJAX_MODEL_LOADER  # noqa
    from flask_admin.model.fields import AjaxSelectField as T_AJAX_SELECT_FIELD  # noqa
    from flask_admin.model.form import (  # noqa
        InlineBaseFormAdmin as T_INLINE_BASE_FORM_ADMIN,
    )
    from flask_admin.model.form import InlineFormAdmin as T_INLINE_FORM_ADMIN
    from flask_admin.model.widgets import (
        InlineFieldListWidget as T_INLINE_FIELD_LIST_WIDGET,
    )
    from flask_admin.model.widgets import InlineFormWidget as T_INLINE_FORM_WIDGET
    from flask_admin.model.widgets import (
        AjaxSelect2Widget as T_INLINE_AJAX_SELECT2_WIDGET,
    )
    from flask_admin.model.widgets import XEditableWidget as T_INLINE_X_EDITABLE_WIDGET

    # optional dependencies
    from arrow import Arrow as T_ARROW  # noqa
    from flask_babel import LazyString as T_LAZY_STRING  # noqa

    from flask_sqlalchemy import Model as T_SQLALCHEMY_MODEL
    from peewee import Model as T_PEEWEE_MODEL
    from peewee import Field as T_PEEWEE_FIELD  # noqa
    from pymongo import MongoClient as T_MONGO_CLIENT
    from mongoengine import Document as T_MONGO_ENGINE_CLIENT
    import sqlalchemy  # noqa
    from sqlalchemy import Column as T_SQLALCHEMY_COLUMN
    from sqlalchemy import Table as T_TABLE  # noqa
    from sqlalchemy.orm import InstrumentedAttribute as T_INSTRUMENTED_ATTRIBUTE  # noqa
    from sqlalchemy.orm import scoped_session as T_SQLALCHEMY_SESSION  # noqa
    from sqlalchemy.orm.query import Query
    from sqlalchemy_utils import Choice as T_CHOICE  # noqa
    from sqlalchemy_utils import ChoiceType as T_CHOICE_TYPE  # noqa

    T_SQLALCHEMY_QUERY = Query
    from redis import Redis as T_REDIS  # noqa
    from flask_admin.contrib.peewee.ajax import (
        QueryAjaxModelLoader as T_PEEWEE_QUERY_AJAX_MODEL_LOADER,
    )  # noqa
    from flask_admin.contrib.sqla.ajax import (
        QueryAjaxModelLoader as T_SQLA_QUERY_AJAX_MODEL_LOADER,
    )  # noqa
    from PIL.Image import Image as T_PIL_IMAGE  # noqa
else:
    T_VIEW = "flask_admin.base.BaseView"
    T_INPUT_REQUIRED = "InputRequired"
    T_TIMEZONE_VALIDATOR = "TimeZoneValidator"
    T_UNIQUE = "Unique"
    T_FORM_OPTS = "flask_admin.form.FormOpts"
    T_MODEL_VIEW = "flask_admin.model.BaseModelView"
    T_AJAX_MODEL_LOADER = "flask_admin.model.ajax.AjaxModelLoader"
    T_AJAX_SELECT_FIELD = "flask_admin.model.fields.AjaxSelectField"
    T_INLINE_BASE_FORM_ADMIN = "flask_admin.model.form.InlineBaseFormAdmin"
    T_INLINE_FORM_ADMIN = "flask_admin.model.form.InlineFormAdmin"
    T_INLINE_FIELD_LIST_WIDGET = "flask_admin.model.widgets.InlineFieldListWidget"
    T_INLINE_FORM_WIDGET = "flask_admin.model.widgets.InlineFormWidget"
    T_INLINE_AJAX_SELECT2_WIDGET = "flask_admin.model.widgets.AjaxSelect2Widget"
    T_INLINE_X_EDITABLE_WIDGET = "flask_admin.model.widgets.XEditableWidget"

    T_FIELD_SET = "flask_admin.form.rules.FieldSet"
    T_BASE_RULE = "flask_admin.form.rules.BaseRule"
    T_HEADER = "flask_admin.form.rules.Header"
    T_FLASK_ADMIN_FIELD = "flask_admin.form.rules.Field"
    T_MACRO = "flask_admin.form.rules.Macro"

    # optional dependencies
    T_ARROW = "arrow.Arrow"
    T_LAZY_STRING = "flask_babel.LazyString"
    T_SQLALCHEMY_COLUMN = "sqlalchemy.Column"
    T_SQLALCHEMY_MODEL = "flask_sqlalchemy.Model"
    T_PEEWEE_FIELD = "peewee.Field"
    T_PEEWEE_MODEL = "peewee.Model"
    T_MONGO_CLIENT = "pymongo.MongoClient"
    T_MONGO_ENGINE_CLIENT = "mongoengine.Document"
    T_TABLE = "sqlalchemy.Table"
    T_CHOICE_TYPE = "sqlalchemy_utils.ChoiceType"
    T_CHOICE = "sqlalchemy_utils.Choice"

    T_SQLALCHEMY_QUERY = "sqlalchemy.orm.query.Query"
    T_INSTRUMENTED_ATTRIBUTE = "sqlalchemy.orm.InstrumentedAttribute"
    T_SQLALCHEMY_SESSION = "sqlalchemy.orm.scoped_session"
    T_REDIS = "redis.Redis"
    T_PEEWEE_QUERY_AJAX_MODEL_LOADER = (
        "flask_admin.contrib.peewee.ajax.QueryAjaxModelLoader"
    )
    T_SQLA_QUERY_AJAX_MODEL_LOADER = (
        "flask_admin.contrib.sqla.ajax.QueryAjaxModelLoader"
    )
    T_PIL_IMAGE = "PIL.Image.Image"

T_COLUMN = t.Union[str, T_SQLALCHEMY_COLUMN]
T_FILTER = tuple[int, T_COLUMN, str]
T_ORM_COLUMN = t.Union[T_COLUMN, T_PEEWEE_FIELD]
T_COLUMN_LIST = t.Sequence[
    t.Union[
        T_ORM_COLUMN, t.Iterable[T_ORM_COLUMN], tuple[str, tuple[T_ORM_COLUMN, ...]]
    ]
]
T_CONTRAVARIANT_MODEL_VIEW = t.TypeVar(
    "T_CONTRAVARIANT_MODEL_VIEW", bound=T_MODEL_VIEW, contravariant=True
)
T_FORMATTER = t.Callable[
    [T_CONTRAVARIANT_MODEL_VIEW, t.Optional[Context], t.Any, str], t.Union[str, Markup]
]
T_COLUMN_FORMATTERS = dict[str, T_FORMATTER]
T_TYPE_FORMATTER = t.Callable[[T_MODEL_VIEW, t.Any, str], t.Union[str, Markup]]
T_COLUMN_TYPE_FORMATTERS = dict[type, T_TYPE_FORMATTER]
T_TRANSLATABLE = t.Union[str, T_LAZY_STRING]
# Compatibility for 3-tuples and 4-tuples in iter_choices
# https://wtforms.readthedocs.io/en/3.2.x/changes/#version-3-2-0
T_ITER_CHOICES = t.Union[
    tuple[t.Any, T_TRANSLATABLE, bool, dict[str, t.Any]],
    tuple[t.Any, T_TRANSLATABLE, bool],
]
T_OPTION = tuple[str, T_TRANSLATABLE]
T_OPTION_LIST = t.Sequence[T_OPTION]
T_OPTIONS = t.Union[None, T_OPTION_LIST, t.Callable[[], T_OPTION_LIST]]
T_ORM_MODEL = t.Union[
    T_SQLALCHEMY_MODEL, T_PEEWEE_MODEL, T_MONGO_CLIENT, T_MONGO_ENGINE_CLIENT
]
T_QUERY_AJAX_MODEL_LOADER = t.Union[
    T_PEEWEE_QUERY_AJAX_MODEL_LOADER, T_SQLA_QUERY_AJAX_MODEL_LOADER
]
T_RESPONSE = t.Union[Response, Wkzg_Response]
T_SQLALCHEMY_INLINE_MODELS = t.Sequence[
    t.Union[
        T_INLINE_FORM_ADMIN,
        type[T_SQLALCHEMY_MODEL],
        tuple[type[T_SQLALCHEMY_MODEL], dict[str, t.Any]],
    ]
]
T_RULES_SEQUENCE = t.Sequence[
    t.Union[str, T_FIELD_SET, T_BASE_RULE, T_HEADER, T_FLASK_ADMIN_FIELD, T_MACRO]
]
T_VALIDATOR = t.Union[
    t.Callable[[t.Any, t.Any], t.Any],
    T_UNIQUE,
    T_INPUT_REQUIRED,
    wtforms.validators.Optional,
    wtforms.validators.Length,
    wtforms.validators.AnyOf,
    wtforms.validators.Email,
    wtforms.validators.URL,
    wtforms.validators.IPAddress,
    T_TIMEZONE_VALIDATOR,
    wtforms.validators.NumberRange,
    wtforms.validators.MacAddress,
]
T_PATH_LIKE = t.Union[str, bytes, PathLike[str], PathLike[bytes]]


class WidgetProtocol(t.Protocol):
    def __call__(self, field: Field, **kwargs: t.Any) -> t.Union[str, Markup]: ...


T_WIDGET = t.Union[
    Input,
    T_INLINE_FIELD_LIST_WIDGET,
    T_INLINE_FORM_WIDGET,
    T_INLINE_AJAX_SELECT2_WIDGET,
    T_INLINE_X_EDITABLE_WIDGET,
    WidgetProtocol,
]

T_WIDGET_TYPE = t.Optional[
    t.Union[
        t.Literal[
            "daterangepicker",
            "datetimepicker",
            "datetimerangepicker",
            "datepicker",
            "select2-tags",
            "timepicker",
            "timerangepicker",
            "uuid",
        ],
        str,
    ]
]


class T_FIELD_ARGS_DESCRIPTION(t.TypedDict, total=False):
    description: NotRequired[str]


class T_FIELD_ARGS_FILTERS(t.TypedDict):
    filters: NotRequired[list[t.Callable[[t.Any], t.Any]]]
    allow_blank: NotRequired[bool]
    choices: NotRequired[t.Union[list[tuple[int, str]], list[Enum]]]
    validators: NotRequired[list[T_VALIDATOR]]
    coerce: NotRequired[t.Callable[[t.Any], t.Any]]


class T_FIELD_ARGS_LABEL(t.TypedDict):
    label: NotRequired[str]


class T_FIELD_ARGS_PLACES(t.TypedDict):
    places: t.Optional[UnsetValue]


class T_FIELD_ARGS_VALIDATORS(t.TypedDict, total=False):
    label: NotRequired[str]
    description: NotRequired[str]
    filters: NotRequired[list[t.Callable[[t.Any], t.Any]]]
    default: NotRequired[t.Any]
    widget: NotRequired[Input]
    validators: NotRequired[list[T_VALIDATOR]]
    render_kw: NotRequired[dict[str, t.Any]]
    name: NotRequired[str]
    _form: NotRequired[BaseForm]
    _prefix: NotRequired[str]


class T_FIELD_ARGS_VALIDATORS_ALLOW_BLANK(T_FIELD_ARGS_VALIDATORS):
    allow_blank: NotRequired[bool]


class T_FIELD_ARGS_VALIDATORS_FILES(T_FIELD_ARGS_VALIDATORS):
    base_path: NotRequired[str]
    allow_overwrite: NotRequired[bool]


# wtfforms types
class _MultiDictLikeBase(t.Protocol):
    def __iter__(self) -> t.Iterator[str]: ...
    def __len__(self) -> int: ...
    def __contains__(self, key: t.Any, /) -> bool: ...


class _MultiDictLikeWithGetlist(_MultiDictLikeBase, t.Protocol):
    def getlist(self, key: str, /) -> list[t.Any]: ...
