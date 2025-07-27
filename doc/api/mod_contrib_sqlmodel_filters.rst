``flask_admin.contrib.sqlmodel.filters``
=========================================

SQLModel filter implementations with support for computed properties and post-query filtering.

This module provides comprehensive filtering support for SQLModel fields including:

* **Standard field filtering**: Database-level filtering for regular SQLModel fields
* **Property filtering**: Post-query filtering for computed properties using special markers
* **Type-specific filters**: Dedicated filter classes for different data types
* **Advanced filtering**: Between filters, in-list filters, and custom filter logic

.. automodule:: flask_admin.contrib.sqlmodel.filters

    .. autoclass:: BaseSQLModelFilter
        :members:

    .. autoclass:: FilterEqual
        :members:

    .. autoclass:: FilterNotEqual
        :members:

    .. autoclass:: FilterLike
        :members:

    .. autoclass:: FilterNotLike
        :members:

    .. autoclass:: FilterGreater
        :members:

    .. autoclass:: FilterSmaller
        :members:

    .. autoclass:: FilterEmpty
        :members:

    .. autoclass:: FilterInList
        :members:

    .. autoclass:: FilterNotInList
        :members:

    .. autoclass:: BooleanEqualFilter
        :members:

    .. autoclass:: BooleanNotEqualFilter
        :members:

    .. autoclass:: IntEqualFilter
        :members:

    .. autoclass:: IntNotEqualFilter
        :members:

    .. autoclass:: IntGreaterFilter
        :members:

    .. autoclass:: IntSmallerFilter
        :members:

    .. autoclass:: IntInListFilter
        :members:

    .. autoclass:: IntNotInListFilter
        :members:

    .. autoclass:: FloatEqualFilter
        :members:

    .. autoclass:: FloatNotEqualFilter
        :members:

    .. autoclass:: FloatGreaterFilter
        :members:

    .. autoclass:: FloatSmallerFilter
        :members:

    .. autoclass:: FloatInListFilter
        :members:

    .. autoclass:: FloatNotInListFilter
        :members:

    .. autoclass:: DateEqualFilter
        :members:

    .. autoclass:: DateNotEqualFilter
        :members:

    .. autoclass:: DateGreaterFilter
        :members:

    .. autoclass:: DateSmallerFilter
        :members:

    .. autoclass:: DateBetweenFilter
        :members:

    .. autoclass:: DateNotBetweenFilter
        :members:

    .. autoclass:: DateTimeEqualFilter
        :members:

    .. autoclass:: DateTimeNotEqualFilter
        :members:

    .. autoclass:: DateTimeGreaterFilter
        :members:

    .. autoclass:: DateTimeSmallerFilter
        :members:

    .. autoclass:: DateTimeBetweenFilter
        :members:

    .. autoclass:: DateTimeNotBetweenFilter
        :members:

    .. autoclass:: TimeEqualFilter
        :members:

    .. autoclass:: TimeNotEqualFilter
        :members:

    .. autoclass:: TimeGreaterFilter
        :members:

    .. autoclass:: TimeSmallerFilter
        :members:

    .. autoclass:: TimeBetweenFilter
        :members:

    .. autoclass:: TimeNotBetweenFilter
        :members:

    .. autoclass:: FilterConverter
        :members:
