import datetime
import time
import typing as t
import uuid

from flask_admin._types import T_MODEL_VIEW
from flask_admin._types import T_OPTION_LIST
from flask_admin._types import T_OPTIONS
from flask_admin._types import T_TRANSLATABLE
from flask_admin._types import T_WIDGET_TYPE
from flask_admin.babel import lazy_gettext


class BaseFilter:
    """
    Base filter class.
    """

    def __init__(
        self,
        name: str,
        options: T_OPTIONS = None,
        data_type: T_WIDGET_TYPE = None,
        key_name: str | None = None,
    ) -> None:
        """
        Constructor.

        :param name:
            Displayed name
        :param options:
            List of fixed options. If provided, will use drop down instead of textbox.
        :param data_type:
            Client-side widget type to use.
        :param key_name:
            Optional name who represent this filter.
        """
        self.name = name
        self.options = options
        self.data_type = data_type
        self.key_name = key_name

    def get_options(self, view: T_MODEL_VIEW) -> T_OPTION_LIST | None:
        """
        Return list of predefined options.

        Override to customize behavior.

        :param view:
            Associated administrative view class.
        """
        options = self.options

        if options:
            if callable(options):
                options = options()

            return options

        return None

    def validate(self, value: t.Any) -> bool:
        """
        Validate value.

        If value is valid, returns `True` and `False` otherwise.

        :param value:
            Value to validate
        """
        # useful for filters with date conversions, see if conversion in clean()
        # raises ValueError
        try:
            self.clean(value)
            return True
        except ValueError:
            return False

    def clean(self, value: t.Any) -> t.Any:
        """
        Parse value into python format. Occurs before .apply()

        :param value:
            Value to parse
        """
        return value

    def apply(self, query: t.Any, value: t.Any) -> t.Any:
        """
        Apply search criteria to the query and return new query.

        :param query:
            Query
        :param value:
            Search criteria
        """
        raise NotImplementedError()

    def operation(self) -> T_TRANSLATABLE:
        """
        Return readable operation name.

        For example: u'equals'
        """
        raise NotImplementedError()

    def __unicode__(self) -> str:
        return self.name


# Customized filters
class BaseBooleanFilter(BaseFilter):
    """
    Base boolean filter, uses fixed list of options.
    """

    def __init__(
        self, name: str, options: T_OPTIONS = None, data_type: T_WIDGET_TYPE = None
    ) -> None:
        super().__init__(
            name, (("1", lazy_gettext("Yes")), ("0", lazy_gettext("No"))), data_type
        )

    def validate(self, value: str) -> bool:
        return value in ("0", "1")


class BaseIntFilter(BaseFilter):
    """
    Base Int filter. Adds validation and changes value to python int.

    Avoid using int(float(value)) to also allow using decimals, because it
    causes precision issues with large numbers.
    """

    def clean(self, value: str) -> int:
        return int(value)


class BaseFloatFilter(BaseFilter):
    """
    Base Float filter. Adds validation and changes value to python float.
    """

    def clean(self, value: str) -> float:
        return float(value)


class BaseIntListFilter(BaseFilter):
    """
    Base Integer list filter. Adds validation for int "In List" filter.

    Avoid using int(float(value)) to also allow using decimals, because it
    causes precision issues with large numbers.
    """

    def clean(self, value: str) -> list[int]:
        return [int(v.strip()) for v in value.split(",") if v.strip()]


class BaseFloatListFilter(BaseFilter):
    """
    Base Float list filter. Adds validation for float "In List" filter.
    """

    def clean(self, value: str) -> list[float]:
        return [float(v.strip()) for v in value.split(",") if v.strip()]


class BaseDateFilter(BaseFilter):
    """
    Base Date filter. Uses client-side date picker control.
    """

    def __init__(
        self, name: str, options: T_OPTIONS = None, data_type: T_WIDGET_TYPE = None
    ):
        super().__init__(name, options, data_type="datepicker")

    def clean(self, value: str) -> datetime.date:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()


class BaseDateBetweenFilter(BaseFilter):
    """
    Base Date Between filter. Consolidates logic for validation and clean.
    Apply method is different for each back-end.
    """

    def clean(self, value: str) -> list[datetime.date]:
        return [
            datetime.datetime.strptime(range, "%Y-%m-%d").date()
            for range in value.split(" to ")
        ]

    def operation(self) -> T_TRANSLATABLE:
        return lazy_gettext("between")

    def validate(self, value: str) -> bool:
        try:
            value = [
                datetime.datetime.strptime(range, "%Y-%m-%d").date()
                for range in value.split(" to ")
            ]  # type: ignore[assignment]
            # if " to " is missing, fail validation
            # sqlalchemy's .between() will not work if end date is before start date
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False
        except ValueError:
            return False


class BaseDateTimeFilter(BaseFilter):
    """
    Base DateTime filter. Uses client-side date time picker control.
    """

    def __init__(
        self, name: str, options: T_OPTIONS = None, data_type: T_WIDGET_TYPE = None
    ) -> None:
        super().__init__(name, options, data_type="datetimepicker")

    def clean(self, value: str) -> datetime.datetime:
        # datetime filters will not work in SQLite + SQLAlchemy if value not converted
        # to datetime
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


class BaseDateTimeBetweenFilter(BaseFilter):
    """
    Base DateTime Between filter. Consolidates logic for validation and clean.
    Apply method is different for each back-end.
    """

    def clean(self, value: str) -> list[datetime.datetime]:
        return [
            datetime.datetime.strptime(range, "%Y-%m-%d %H:%M:%S")
            for range in value.split(" to ")
        ]

    def operation(self) -> str:
        return lazy_gettext("between")

    def validate(self, value: str) -> bool:
        try:
            value = [  # type: ignore[assignment]
                datetime.datetime.strptime(range, "%Y-%m-%d %H:%M:%S")
                for range in value.split(" to ")
            ]
            if (len(value) == 2) and (value[0] <= value[1]):
                return True
            else:
                return False
        except ValueError:
            return False


class BaseTimeFilter(BaseFilter):
    """
    Base Time filter. Uses client-side time picker control.
    """

    def __init__(
        self, name: str, options: T_OPTIONS = None, data_type: T_WIDGET_TYPE = None
    ) -> None:
        super().__init__(name, options, data_type="timepicker")

    def clean(self, value: str) -> datetime.time:
        # time filters will not work in SQLite + SQLAlchemy if value not converted
        # to time
        timetuple = time.strptime(value, "%H:%M:%S")
        return datetime.time(timetuple.tm_hour, timetuple.tm_min, timetuple.tm_sec)


class BaseTimeBetweenFilter(BaseFilter):
    """
    Base Time Between filter. Consolidates logic for validation and clean.
    Apply method is different for each back-end.
    """

    def clean(self, value: str) -> list[datetime.time]:
        timetuples = [time.strptime(range, "%H:%M:%S") for range in value.split(" to ")]
        return [
            datetime.time(timetuple.tm_hour, timetuple.tm_min, timetuple.tm_sec)
            for timetuple in timetuples
        ]

    def operation(self) -> str:
        return lazy_gettext("between")

    def validate(self, value: str) -> bool:
        try:
            timetuples = [
                time.strptime(range, "%H:%M:%S") for range in value.split(" to ")
            ]
            if (len(timetuples) == 2) and (timetuples[0] <= timetuples[1]):
                return True
            else:
                return False
        except ValueError:
            raise
            return False


class BaseUuidFilter(BaseFilter):
    """
    Base uuid filter
    """

    def __init__(
        self, name: str, options: T_OPTIONS = None, data_type: T_WIDGET_TYPE = None
    ) -> None:
        super().__init__(name, options, data_type="uuid")

    def clean(self, value: str) -> t.Any:
        value = uuid.UUID(value)  # type: ignore[assignment]
        return str(value)


class BaseUuidListFilter(BaseFilter):
    """
    Base uuid list filter
    """

    def clean(self, value: str) -> list[str]:
        return [str(uuid.UUID(v.strip())) for v in value.split(",") if v.strip()]


def convert(*args: t.Any) -> t.Callable[..., t.Any]:
    """
    Decorator for field to filter conversion routine.

    See :mod:`flask_admin.contrib.sqla.filters` for usage example.
    """

    def _inner(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        func._converter_for = list(map(lambda x: x.lower(), args))  # type: ignore[attr-defined]
        return func

    return _inner


class BaseFilterConverter:
    """
    Base filter converter.

    Derive from this class to implement custom field to filter conversion
    logic.
    """

    def __init__(self) -> None:
        self.converters = dict()

        for p in dir(self):
            attr = getattr(self, p)

            if hasattr(attr, "_converter_for"):
                for p in attr._converter_for:
                    self.converters[p] = attr
