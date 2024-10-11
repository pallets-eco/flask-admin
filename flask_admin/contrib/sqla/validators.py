from sqlalchemy.orm.exc import NoResultFound
from wtforms import ValidationError
from wtforms.validators import InputRequired

from flask_admin._compat import filter_list
from flask_admin.babel import lazy_gettext


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

    def __init__(self, db_session, model, column, message=None):
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message or lazy_gettext("Already exists.")

    def __call__(self, form, field):
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


def valid_currency(form, field):
    from sqlalchemy_utils import Currency

    try:
        Currency(field.data)
    except (TypeError, ValueError) as err:
        raise ValidationError(
            field.gettext("Not a valid ISO currency code (e.g. USD, EUR, CNY).")
        ) from err


def valid_color(form, field):
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

    def __init__(self, coerce_function):
        self.coerce_function = coerce_function

    def __call__(self, form, field):
        try:
            self.coerce_function(str(field.data))
        except Exception as err:
            msg = (
                'Not a valid timezone (e.g. "America/New_York", '
                '"Africa/Johannesburg", "Asia/Singapore").'
            )
            raise ValidationError(field.gettext(msg)) from err
