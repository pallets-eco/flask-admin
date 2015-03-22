from flask_admin.model.typefmt import BASE_FORMATTERS, list_formatter
from sqlalchemy.orm.collections import InstrumentedList


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS.update({
    InstrumentedList: list_formatter
})
