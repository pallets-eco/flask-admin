"""
SQLModel type formatters for Flask-Admin.

This module provides type-specific formatting functions for displaying
SQLModel field values in Flask-Admin list and detail views.
Includes formatters for enums, dates, and other SQLModel-specific types.
"""

import typing as t
from enum import Enum

from flask_admin.model.typefmt import BASE_FORMATTERS
from flask_admin.model.typefmt import EXPORT_FORMATTERS
from flask_admin.model.typefmt import list_formatter

from ..._types import T_MODEL_VIEW


def enum_formatter(view: T_MODEL_VIEW, enum_member: Enum, name: str) -> str:
    """
    Return the value of an Enum member.

    :param enum_member:
        The Enum member.
    """
    return enum_member.value


def arrow_formatter(view: T_MODEL_VIEW, arrow_time: t.Any, name: str) -> str:
    """
    Return a human-friendly string of the time relative to now.
    See https://arrow.readthedocs.io/

    :param arrow_time:
        An Arrow object for handling datetimes.
    """
    return arrow_time.humanize()


def arrow_export_formatter(view, arrow_time, name) -> str:
    """
    Return the string representation of an Arrow object.
    See https://arrow.readthedocs.io/

    :param arrow_time:
        An Arrow object for handling datetimes.
    """
    return arrow_time.format()


# Copy the base formatters
DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
EXPORT_FORMATTERS = EXPORT_FORMATTERS.copy()

# Add formatters for standard Python types used by SQLModel
DEFAULT_FORMATTERS.update(
    {
        list: list_formatter,
        Enum: enum_formatter,
    }
)

# Add optional formatters if the libraries are installed
try:
    from arrow import Arrow

    DEFAULT_FORMATTERS[Arrow] = arrow_formatter
    EXPORT_FORMATTERS[Arrow] = arrow_export_formatter
except ImportError:
    # Arrow library is not installed, skipping
    pass
