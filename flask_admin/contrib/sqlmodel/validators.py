"""
SQLModel validators for Flask-Admin forms.

This module provides validation functions and classes for SQLModel forms,
including uniqueness validation, currency validation, color validation,
and other common field validators.
"""

import typing as t

from sqlmodel import select
from wtforms import ValidationError
from wtforms.validators import InputRequired

from flask_admin._compat import filter_list
from flask_admin.babel import lazy_gettext

from ..._types import T_SQLALCHEMY_MODEL
from ..._types import T_SQLALCHEMY_SESSION
from ..._types import T_TRANSLATABLE


class Unique:
    """Checks field value unicity against specified table field.

    :param db_session:
        A SQLModel Session instance.
    :param model:
        The SQLModel model to check unicity against.
    :param column:
        The unique column.
    :param message:
        The error message.
    """

    field_flags = {"unique": True}

    def __init__(
        self,
        db_session: T_SQLALCHEMY_SESSION,
        model: T_SQLALCHEMY_MODEL,
        column: t.Any,
        message: t.Optional[T_TRANSLATABLE] = None,
    ) -> None:
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message or lazy_gettext("Already exists.")

    def __call__(self, form: t.Any, field: t.Any) -> None:
        # databases allow multiple NULL values for unique columns
        if field.data is None:
            return

        try:
            obj = self.db_session.exec(
                select(self.model).where(self.column == field.data)
            ).one()

            if not hasattr(form, "_obj") or not form._obj == obj:
                raise ValidationError(str(self.message))
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception:
            # No result found or other database error -
            # this is OK for uniqueness validation
            pass


class ItemsRequired(InputRequired):
    """
    A version of the ``InputRequired`` validator that works with relations,
    to require a minimum number of related items.
    """

    def __init__(self, min=1, message=None):
        super().__init__(message=message)
        self.min = min

    def __call__(self, form, field):
        items = filter_list(lambda e: not field.should_delete(e), field.entries)
        if len(items) < self.min:
            if self.message is None:
                message = field.ngettext(
                    "At least %(num)d item is required",
                    "At least %(num)d items are required",
                    self.min,
                )
            else:
                message = self.message

            raise ValidationError(message)


# Note: SQLAlchemy-utils specific validators have been moved to
# SQLAlchemyExtendedMixin in mixins.py for better dependency management
