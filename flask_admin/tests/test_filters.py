import enum
import typing as t
from datetime import date
from datetime import datetime
from datetime import time

import pytest
from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import Flask

from flask_admin.base import Admin
from flask_admin.contrib.mongoengine import filters as mofilters
from flask_admin.contrib.peewee import filters as peefilters
from flask_admin.contrib.pymongo import filters as pymofilters
from flask_admin.contrib.sqla import filters as safilters
from flask_admin.model import filters


class Day(enum.Enum):
    SATURDAY = 6
    SUNDAY = 7


def create_filter_clean_params() -> list[tuple[t.Any, ...]]:
    params: list[t.Any] = []
    all_filter_classes: list[type[filters.BaseFilter]] = []
    all = (
        list(peefilters.__dict__.values())
        + list(mofilters.__dict__.values())
        + list(pymofilters.__dict__.values())
        + list(safilters.__dict__.values())
    )

    for FilterClass in all:
        if isinstance(FilterClass, type) and issubclass(
            FilterClass, filters.BaseFilter
        ):
            all_filter_classes.append(FilterClass)

    for FilterClass in all_filter_classes:
        if issubclass(FilterClass, filters.BaseBooleanFilter):
            params.append((FilterClass, "1", ("1", True), None))
            params.append((FilterClass, "0", ("0", False), None))

        if issubclass(FilterClass, filters.BaseEmptyFilter):
            params.append((FilterClass, "1", "1", None))
            params.append((FilterClass, "0", "0", None))

        if issubclass(FilterClass, filters.BaseIntFilter):
            params.append((FilterClass, "", ValueError, None))
            params.append((FilterClass, "15", 15, None))
            params.append((FilterClass, "-48", -48, None))
            params.append((FilterClass, "2.1", ValueError, None))

        if issubclass(FilterClass, filters.BaseFloatFilter):
            params.append((FilterClass, "", ValueError, None))
            params.append((FilterClass, "15", 15.0, "15.0"))
            params.append((FilterClass, "-48.3", -48.3, None))
            params.append((FilterClass, "2.1", 2.1, None))

        if issubclass(FilterClass, filters.BaseIntListFilter):
            params.append((FilterClass, "", [], None))
            params.append((FilterClass, "15", [15], None))
            params.append((FilterClass, "2,1", [2, 1], None))

        if issubclass(FilterClass, filters.BaseFloatListFilter):
            params.append((FilterClass, "", [], None))
            params.append((FilterClass, "15", [15.0], "15.0"))
            params.append((FilterClass, "15,16", [15.0, 16.0], "15.0,16.0"))
            params.append((FilterClass, "-48.3", [-48.3], None))
            params.append((FilterClass, "2.1,3.4", [2.1, 3.4], None))

        if issubclass(FilterClass, filters.BaseDateFilter):
            params.append((FilterClass, "2026-01-28", date(2026, 1, 28), None))
            params.append((FilterClass, "2026-30-05", ValueError, None))

        if issubclass(FilterClass, filters.BaseDateBetweenFilter):
            params.append(
                (
                    FilterClass,
                    "2026-01-15 to 2026-01-20",
                    [date(2026, 1, 15), date(2026, 1, 20)],
                    None,
                )
            )
            params.append((FilterClass, "2026-30-05", ValueError, None))

        if issubclass(FilterClass, filters.BaseDateTimeFilter):
            params.append(
                (
                    FilterClass,
                    "2026-01-28 15:00:00",
                    datetime(2026, 1, 28, 15, 0, 0),
                    None,
                ),
            )
            params.append(
                (FilterClass, "2026-02-30 15:00:00", ValueError, None)
            )  # Invalid date
            params.append(
                (FilterClass, "2026-05-05 03:00:00 AM", ValueError, None)
            )  # Invalid format

        if issubclass(FilterClass, filters.BaseDateTimeBetweenFilter):
            params.append(
                (
                    FilterClass,
                    "2026-01-15 00:00:00 to 2026-01-20 00:00:00",
                    [datetime(2026, 1, 15), datetime(2026, 1, 20)],
                    None,
                )
            )

        if issubclass(FilterClass, filters.BaseTimeFilter):
            params.append((FilterClass, "15:00:00", time(15, 0, 0), None))
            params.append((FilterClass, "03:00:00 AM", ValueError, None))

        if issubclass(FilterClass, filters.BaseTimeBetweenFilter):
            params.append(
                (
                    FilterClass,
                    "15:00:00 to 20:00:00",
                    [time(15, 0, 0), time(20, 0, 0)],
                    None,
                )
            )

        # FIXME: test is skipped unexpectedly, need to investigate.
        # if issubclass(FilterClass, filters.BaseUuidFilter):
        #     v= uuid.uuid4()
        #     params.append((FilterClass, str(v), v))

        if issubclass(FilterClass, mofilters.ReferenceObjectIdFilter):
            id = "507f1f77bcf86cd799439011"
            v = ObjectId(id)
            params.append((FilterClass, id, ObjectId(str(v).strip()), None))
            params.append((FilterClass, "invalid-objectid", InvalidId, None))

        if (
            issubclass(FilterClass, safilters.EnumEqualFilter)
            or issubclass(FilterClass, safilters.EnumFilterNotEqual)
            or issubclass(FilterClass, safilters.ChoiceTypeEqualFilter)
            or issubclass(FilterClass, safilters.ChoiceTypeNotEqualFilter)
        ):
            params.append((FilterClass, "SATURDAY", Day.SATURDAY.name, None))

        if issubclass(FilterClass, safilters.EnumFilterEmpty) or issubclass(
            FilterClass, safilters.ChoiceTypeEmptyFilter
        ):
            params.append((FilterClass, "0", "0", None))
            params.append((FilterClass, "1", "1", None))

        if issubclass(FilterClass, safilters.EnumFilterInList) or issubclass(
            FilterClass, safilters.EnumFilterNotInList
        ):
            params.append(
                (
                    FilterClass,
                    "SATURDAY, SUNDAY",
                    [Day.SATURDAY.name, Day.SUNDAY.name],
                    "SATURDAY,SUNDAY",
                )
            )

        if issubclass(FilterClass, safilters.ChoiceTypeLikeFilter) or issubclass(
            FilterClass, safilters.ChoiceTypeNotLikeFilter
        ):
            params.append((FilterClass, "SATURDAY", Day.SATURDAY.name, None))

    # Clean module path for better readability in test output.
    for i, p in enumerate(params):
        Cls = p[0]
        Cls = Cls.__module__.replace("flask_admin.contrib.", "").replace(".filters", "")
        params[i] = (Cls,) + params[i]

    return params


@pytest.mark.parametrize(
    "module, FilterClass, filter_value, cleaned_val, stringified_val",
    create_filter_clean_params(),
)
def test_filter(
    app: Flask,
    admin: Admin,
    module: str,
    FilterClass: type[filters.BaseFilter],
    filter_value: t.Any,
    cleaned_val: t.Any,
    stringified_val: t.Any,
) -> None:
    stringified_val = stringified_val or str(filter_value)
    flt = FilterClass(column="f1", name="F1_LABEL", options=None)
    is_execption = isinstance(cleaned_val, type) and issubclass(cleaned_val, Exception)

    assert flt.column_name() == "f1"

    if is_execption:
        assert not flt.validate(filter_value)
        with pytest.raises(cleaned_val):
            flt.clean(filter_value)
    else:
        assert flt.validate(filter_value)

        actual = flt.clean(filter_value)
        if not isinstance(cleaned_val, tuple):
            cleaned_val = [cleaned_val]

        assert actual in cleaned_val

        assert flt.stringify(actual) == stringified_val
