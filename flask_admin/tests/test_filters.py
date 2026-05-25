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
        if issubclass(FilterClass, filters.BaseBooleanFilter) and not issubclass(
            FilterClass, filters.BaseEmptyFilter
        ):
            params.append((FilterClass, "1", ("1", True)))
            params.append((FilterClass, "0", ("0", False)))

        if issubclass(FilterClass, filters.BaseEmptyFilter):
            params.append((FilterClass, "1", "1"))
            params.append((FilterClass, "0", "0"))

        if issubclass(FilterClass, filters.BaseIntFilter):
            params.append((FilterClass, "", 0))
            params.append((FilterClass, "15", 15))
            params.append((FilterClass, "-48", -48))
            params.append((FilterClass, "2.1", ValueError))

        if issubclass(FilterClass, filters.BaseFloatFilter):
            params.append((FilterClass, "", 0.0))
            params.append((FilterClass, "15", 15.0))
            params.append((FilterClass, "-48.3", -48.3))
            params.append((FilterClass, "2.1", 2.1))

        if issubclass(FilterClass, filters.BaseIntListFilter):
            params.append((FilterClass, "", []))
            params.append((FilterClass, "15", [15]))
            params.append((FilterClass, "2,1", [2, 1]))

        if issubclass(FilterClass, filters.BaseFloatListFilter):
            params.append((FilterClass, "", []))
            params.append((FilterClass, "15", [15.0]))
            params.append((FilterClass, "-48.3", [-48.3]))
            params.append((FilterClass, "2.1,3.4", [2.1, 3.4]))

        if issubclass(FilterClass, filters.BaseDateFilter):
            params.append((FilterClass, "2026-01-28", date(2026, 1, 28)))
            params.append((FilterClass, "2026-30-05", ValueError))

        if issubclass(FilterClass, filters.BaseDateBetweenFilter):
            params.append(
                (
                    FilterClass,
                    "2026-01-15 to 2026-01-20",
                    [date(2026, 1, 15), date(2026, 1, 20)],
                )
            )
            params.append((FilterClass, "2026-30-05", ValueError))

        if issubclass(FilterClass, filters.BaseDateTimeFilter):
            params.append(
                (FilterClass, "2026-01-28 15:00:00", datetime(2026, 1, 28, 15, 0, 0))
            )
            params.append((FilterClass, "2026-05-05 03:00:00 AM", ValueError))

        if issubclass(FilterClass, filters.BaseDateTimeBetweenFilter):
            params.append(
                (
                    FilterClass,
                    "2026-01-15 00:00:00 to 2026-01-20 00:00:00",
                    [datetime(2026, 1, 15), datetime(2026, 1, 20)],
                )
            )

        if issubclass(FilterClass, filters.BaseTimeFilter):
            params.append((FilterClass, "15:00:00", time(15, 0, 0)))
            params.append((FilterClass, "03:00:00 AM", ValueError))

        if issubclass(FilterClass, filters.BaseTimeBetweenFilter):
            params.append(
                (FilterClass, "15:00:00 to 20:00:00", [time(15, 0, 0), time(20, 0, 0)])
            )

        # FIXME: test is skipped unexpectedly, need to investigate.
        # if issubclass(FilterClass, filters.BaseUuidFilter):
        #     v= uuid.uuid4()
        #     params.append((FilterClass, str(v), v))

        if issubclass(FilterClass, mofilters.ReferenceObjectIdFilter):
            v = ObjectId("507f1f77bcf86cd799439011")
            params.append(
                (FilterClass, "507f1f77bcf86cd799439011", ObjectId(str(v).strip()))
            )
            params.append((FilterClass, "invalid-objectid", InvalidId))

        if (
            issubclass(FilterClass, safilters.EnumEqualFilter)
            or issubclass(FilterClass, safilters.EnumFilterNotEqual)
            or issubclass(FilterClass, safilters.ChoiceTypeEqualFilter)
            or issubclass(FilterClass, safilters.ChoiceTypeNotEqualFilter)
        ):
            params.append((FilterClass, "SATURDAY", Day.SATURDAY.name))

        if issubclass(FilterClass, safilters.EnumFilterEmpty) or issubclass(
            FilterClass, safilters.ChoiceTypeEmptyFilter
        ):
            params.append((FilterClass, "0", "0"))
            params.append((FilterClass, "1", "1"))

        if issubclass(FilterClass, safilters.EnumFilterInList) or issubclass(
            FilterClass, safilters.EnumFilterNotInList
        ):
            params.append(
                (FilterClass, "SATURDAY, SUNDAY", [Day.SATURDAY.name, Day.SUNDAY.name])
            )

        if issubclass(FilterClass, safilters.ChoiceTypeLikeFilter) or issubclass(
            FilterClass, safilters.ChoiceTypeNotLikeFilter
        ):
            params.append((FilterClass, "SATURDAY", Day.SATURDAY.name))

    # Clean module path for better readability in test output.
    for i, p in enumerate(params):
        Cls = p[0]
        Cls = Cls.__module__.replace("flask_admin.contrib.", "").replace(".filters", "")
        params[i] = (Cls,) + params[i]

    return params


@pytest.mark.parametrize(
    "module, FilterClass, filter_value, expected_value", create_filter_clean_params()
)
def test_filter_clean(
    app: Flask,
    admin: Admin,
    module: str,
    FilterClass: type[filters.BaseFilter],
    filter_value: t.Any,
    expected_value: t.Any,
) -> None:
    flt = FilterClass(column="f1", name="F1_LABEL", options=None)
    is_execption = isinstance(expected_value, type) and issubclass(
        expected_value, Exception
    )
    if is_execption:
        assert not flt.validate(filter_value)
        with pytest.raises(expected_value):
            flt.clean(filter_value)
    else:
        actual = flt.clean(filter_value)
        expected_value = (
            expected_value if isinstance(expected_value, tuple) else [expected_value]
        )
        assert actual in expected_value
        assert flt.validate(filter_value)
