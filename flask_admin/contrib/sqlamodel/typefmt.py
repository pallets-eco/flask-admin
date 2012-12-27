from flask.ext.admin.model.typefmt import DEFAULT_FORMATTERS, list_formatter
from sqlalchemy.orm.collections import InstrumentedList


DEFAULT_FORMATTERS = DEFAULT_FORMATTERS.copy()
DEFAULT_FORMATTERS.update({
    InstrumentedList: list_formatter
})
