from sqlalchemy.orm.exc import NoResultFound

from wtforms import ValidationError
try:
    from wtforms.validators import InputRequired
except ImportError:
    from wtforms.validators import Required as InputRequired


class Unique(object):
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
    field_flags = ('unique', )

    def __init__(self, db_session, model, column, message=None):
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message

    def __call__(self, form, field):
        # databases allow multiple NULL values for unique columns
        if field.data is None:
            return

        try:
            obj = (self.db_session.query(self.model)
                   .filter(self.column == field.data)
                   .one())

            if not hasattr(form, '_obj') or not form._obj == obj:
                if self.message is None:
                    self.message = field.gettext(u'Already exists.')
                raise ValidationError(self.message)
        except NoResultFound:
            pass


class ItemsRequired(InputRequired):
    """
    A version of the ``InputRequired`` validator that works with relations,
    to require a minimum number of related items.
    """
    def __init__(self, min=1, message=None):
        super(ItemsRequired, self).__init__(message=message)
        self.min = min

    def __call__(self, form, field):
        if len(field.data) < self.min:
            if self.message is None:
                message = field.ngettext(
                    u"At least %(num)d item is required",
                    u"At least %(num)d items are required",
                    self.min
                )
            else:
                message = self.message

            raise ValidationError(message)
