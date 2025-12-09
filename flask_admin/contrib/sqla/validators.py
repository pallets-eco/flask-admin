import typing as t

from sqlalchemy.orm.exc import NoResultFound
from wtforms import Field
from wtforms import Form
from wtforms import ValidationError
from wtforms.form import BaseForm
from wtforms.validators import InputRequired

from flask_admin._compat import filter_list
from flask_admin._types import T_COLUMN
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask_admin._types import T_TRANSLATABLE
from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla._types import T_SCOPED_SESSION


class Unique:
    """Checks field value unicity against specified table field.

    :param get_session:
        A function that return a SQAlchemy Session.
    :param model:
        The model to check unicity against.
    :param column:
        The unique column.
    :param message:
        The error message.
    """

    field_flags = {"unique": True}

    def __init__(
        self,
        db_session: T_SCOPED_SESSION,
        model: type[T_SQLALCHEMY_MODEL],
        column: T_COLUMN,
        message: T_TRANSLATABLE | None = None,
    ) -> None:
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message or lazy_gettext("Already exists.")

    def __call__(self, form: Form, field: Field) -> None:
        # databases allow multiple NULL values for unique columns
        if field.data is None:
            return

        try:
            obj = (
                self.db_session.query(self.model)
                .filter(self.column == field.data)
                .one()
            )

            if not hasattr(form, "_obj") or not form._obj == obj:
                raise ValidationError(str(self.message))
        except NoResultFound:
            pass


class ItemsRequired(InputRequired):
    """
    A version of the ``InputRequired`` validator that works with relations,
    to require a minimum number of related items.
    """

    def __init__(self, min: int = 1, message: T_TRANSLATABLE | None = None):
        super().__init__(message=message)
        self.min = min

    def __call__(self, form: BaseForm, field: Field) -> None:
        items = filter_list(
            lambda e: not field.should_delete(e),  # type:ignore[attr-defined]
            field.entries,  # type:ignore[attr-defined]
        )
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


def valid_currency(form: Form, field: Field) -> None:
    from sqlalchemy_utils import Currency

    try:
        Currency(field.data)
    except (TypeError, ValueError) as err:
        raise ValidationError(
            field.gettext("Not a valid ISO currency code (e.g. USD, EUR, CNY).")
        ) from err


def valid_color(form: Form, field: Field) -> None:
    from colour import Color

    try:
        Color(field.data)
    except ValueError as err:
        raise ValidationError(
            field.gettext('Not a valid color (e.g. "red", "#f00", "#ff0000").')
        ) from err


class TimeZoneValidator:
    """
    Tries to coerce a TimZone object from input data
    """

    def __init__(self, coerce_function: t.Callable[[str], t.Any]) -> None:
        self.coerce_function = coerce_function

    def __call__(self, form: BaseForm, field: Field) -> None:
        try:
            self.coerce_function(str(field.data))
        except Exception as err:
            msg = (
                'Not a valid timezone (e.g. "America/New_York", '
                '"Africa/Johannesburg", "Asia/Singapore").'
            )
            raise ValidationError(field.gettext(msg)) from err
