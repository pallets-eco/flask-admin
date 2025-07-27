"""
SQLAlchemy-utils extended types support mixin for SQLModel forms.

This module provides optional support for SQLAlchemy-utils extended types
through a mixin class that can be composed with the main AdminModelConverter.
"""

import typing as t
from enum import EnumMeta
from typing import Any
from typing import Optional

from wtforms import fields
from wtforms import validators

# Import ValidationError for validators
from wtforms.validators import ValidationError

from flask_admin import form


def avoid_empty_strings(value: t.Any) -> t.Optional[t.Any]:
    """
    Return None if the incoming value is an empty string or whitespace.
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return value


# Optional import strategy with graceful fallback for sqlalchemy-utils
try:
    from sqlalchemy_utils import ArrowType
    from sqlalchemy_utils import ChoiceType
    from sqlalchemy_utils import ColorType
    from sqlalchemy_utils import CurrencyType
    from sqlalchemy_utils import EmailType
    from sqlalchemy_utils import IPAddressType
    from sqlalchemy_utils import TimezoneType
    from sqlalchemy_utils import URLType

    SQLALCHEMY_UTILS_AVAILABLE = True
except ImportError:
    # Create dummy classes for type checking when sqlalchemy-utils is not available
    EmailType = URLType = IPAddressType = ColorType = None
    CurrencyType = TimezoneType = ChoiceType = ArrowType = None
    SQLALCHEMY_UTILS_AVAILABLE = False


# SQLAlchemy-utils specific validators - moved from validators.py
def valid_color(form: t.Any, field: t.Any) -> None:
    """
    Color validator that supports both named colors and hex values.
    Uses the colour library to validate colors just like SQLAlchemy version.
    For full validation, consider using additional color validation libraries.
    """
    if not field.data:
        return

    try:
        import colour

        colour.Color(field.data)
    except ImportError:
        # Basic fallback validation if colour library is not available
        if not _is_basic_color_valid(field.data):
            raise ValidationError("Invalid color format.") from None
    except (ValueError, AttributeError) as err:
        raise ValidationError(f"Invalid color '{field.data}'. Error: {err}") from err


def valid_currency(form: t.Any, field: t.Any) -> None:
    """
    Currency code validator that validates against actual ISO 4217 codes.
    Uses the same validation as SQLAlchemy-Utils CurrencyType.
    """
    if not field.data:
        return

    # First check basic format (3 uppercase letters)
    if not (
        isinstance(field.data, str)
        and len(field.data) == 3
        and field.data.isupper()
        and field.data.isalpha()
    ):
        raise ValidationError(
            f"Invalid currency code '{field.data}'. "
            "Must be a 3-letter ISO 4217 currency code (e.g., USD, EUR)."
        )

    # Validate against actual ISO 4217 codes
    # Use a comprehensive list of valid currency codes
    valid_codes = {
        "AED",
        "AFN",
        "ALL",
        "AMD",
        "ANG",
        "AOA",
        "ARS",
        "AUD",
        "AWG",
        "AZN",
        "BAM",
        "BBD",
        "BDT",
        "BGN",
        "BHD",
        "BIF",
        "BMD",
        "BND",
        "BOB",
        "BRL",
        "BSD",
        "BTN",
        "BWP",
        "BYN",
        "BZD",
        "CAD",
        "CDF",
        "CHF",
        "CLP",
        "CNY",
        "COP",
        "CRC",
        "CUC",
        "CUP",
        "CVE",
        "CZK",
        "DJF",
        "DKK",
        "DOP",
        "DZD",
        "EGP",
        "ERN",
        "ETB",
        "EUR",
        "FJD",
        "FKP",
        "GBP",
        "GEL",
        "GHS",
        "GIP",
        "GMD",
        "GNF",
        "GTQ",
        "GYD",
        "HKD",
        "HNL",
        "HRK",
        "HTG",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "IQD",
        "IRR",
        "ISK",
        "JMD",
        "JOD",
        "JPY",
        "KES",
        "KGS",
        "KHR",
        "KMF",
        "KPW",
        "KRW",
        "KWD",
        "KYD",
        "KZT",
        "LAK",
        "LBP",
        "LKR",
        "LRD",
        "LSL",
        "LYD",
        "MAD",
        "MDL",
        "MGA",
        "MKD",
        "MMK",
        "MNT",
        "MOP",
        "MRU",
        "MUR",
        "MVR",
        "MWK",
        "MXN",
        "MYR",
        "MZN",
        "NAD",
        "NGN",
        "NIO",
        "NOK",
        "NPR",
        "NZD",
        "OMR",
        "PAB",
        "PEN",
        "PGK",
        "PHP",
        "PKR",
        "PLN",
        "PYG",
        "QAR",
        "RON",
        "RSD",
        "RUB",
        "RWF",
        "SAR",
        "SBD",
        "SCR",
        "SDG",
        "SEK",
        "SGD",
        "SHP",
        "SLE",
        "SLL",
        "SOS",
        "SRD",
        "STN",
        "SYP",
        "SZL",
        "THB",
        "TJS",
        "TMT",
        "TND",
        "TOP",
        "TRY",
        "TTD",
        "TVD",
        "TWD",
        "TZS",
        "UAH",
        "UGX",
        "USD",
        "UYU",
        "UZS",
        "VED",
        "VES",
        "VND",
        "VUV",
        "WST",
        "XAF",
        "XCD",
        "XDR",
        "XOF",
        "XPF",
        "YER",
        "ZAR",
        "ZMW",
        "ZWL",
    }

    if field.data not in valid_codes:
        raise ValidationError(
            f"Invalid currency code '{field.data}'. "
            "Must be a valid ISO 4217 currency code (e.g., USD, EUR, GBP)."
        )


class TimeZoneValidator:
    """
    Tries to coerce a TimeZone object from input data
    """

    def __init__(
        self, coerce_function: t.Optional[t.Callable[[t.Any], t.Any]] = None
    ) -> None:
        self.coerce_function = coerce_function

    def __call__(self, form: t.Any, field: t.Any) -> None:
        if not field.data:
            return

        if self.coerce_function:
            try:
                self.coerce_function(field.data)
            except (ValueError, TypeError) as err:
                raise ValidationError(
                    f"Invalid timezone '{field.data}'. Error: {err}"
                ) from err
        else:
            # Basic timezone validation fallback
            try:
                import pytz

                pytz.timezone(field.data)
            except ImportError:
                # If pytz is not available, do basic validation
                if not isinstance(field.data, str) or len(field.data.strip()) == 0:
                    raise ValidationError("Invalid timezone format.") from None
            except Exception as err:
                raise ValidationError(
                    f"Invalid timezone '{field.data}'. Error: {err}"
                ) from err


def _is_basic_color_valid(color_value: str) -> bool:
    """Basic color validation without external libraries."""
    if not isinstance(color_value, str):
        return False

    color_value = color_value.strip().lower()

    # Check for hex colors
    if color_value.startswith("#"):
        hex_part = color_value[1:]
        if len(hex_part) in (3, 6) and all(c in "0123456789abcdef" for c in hex_part):
            return True

    # Check for basic named colors
    basic_colors = {
        "red",
        "green",
        "blue",
        "yellow",
        "orange",
        "purple",
        "pink",
        "black",
        "white",
        "gray",
        "grey",
        "brown",
        "cyan",
        "magenta",
        "navy",
        "maroon",
        "olive",
        "lime",
        "aqua",
        "teal",
        "silver",
    }

    return color_value in basic_colors


class SQLAlchemyExtendedMixin:
    """
    Mixin for handling SQLAlchemy-utils extended types.

    This mixin provides support for SQLAlchemy-utils field types when the
    sqlalchemy-utils package is available. If the package is not installed,
    the methods gracefully return None, allowing the main converter to handle
    the fields as regular SQLAlchemy types.

    Supported Types:
    - EmailType: Email validation
    - URLType: URL validation
    - IPAddressType: IP address validation
    - ColorType: Color validation (hex, named colors)
    - CurrencyType: Currency code validation
    - TimezoneType: Timezone validation
    - ChoiceType: Choice enumeration fields
    - ArrowType: Arrow datetime fields
    """

    def handle_extended_types(
        self, model: Any, column: Any, field_args: dict, **extra
    ) -> Optional[Any]:
        """
        Handle SQLAlchemy-utils extended types.

        Args:
            model: SQLModel class
            column: SQLAlchemy column object
            field_args: Field arguments dictionary
            extra (kwargs): Additional arguments

        Returns:
            WTForms field instance if handled, None otherwise
        """
        if not SQLALCHEMY_UTILS_AVAILABLE:
            return None

        column_type = getattr(column, "type", None)
        if not column_type:
            return None

        # Email Type
        if EmailType and isinstance(column_type, EmailType):
            return self._convert_email_type(column, field_args, **extra)

        # URL Type
        elif URLType and isinstance(column_type, URLType):
            return self._convert_url_type(field_args, **extra)

        # IP Address Type
        elif IPAddressType and isinstance(column_type, IPAddressType):
            return self._convert_ip_address_type(field_args, **extra)

        # Color Type
        elif ColorType and isinstance(column_type, ColorType):
            return self._convert_color_type(field_args, **extra)

        # Currency Type
        elif CurrencyType and isinstance(column_type, CurrencyType):
            return self._convert_currency_type(field_args, **extra)

        # Timezone Type
        elif TimezoneType and isinstance(column_type, TimezoneType):
            return self._convert_timezone_type(column, field_args, **extra)

        # Choice Type
        elif ChoiceType and isinstance(column_type, ChoiceType):
            return self._convert_choice_type(column, field_args, **extra)

        # Arrow Type
        elif ArrowType and isinstance(column_type, ArrowType):
            return self._convert_arrow_type(field_args, **extra)

        return None

    def _convert_email_type(
        self, column: Any, field_args: dict, **extra
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils EmailType to StringField with email validation."""
        # Apply nullable common logic if available
        if hasattr(self, "_nullable_common"):
            self._nullable_common(column, field_args)

        field_args["validators"].append(validators.Email())
        return fields.StringField(**field_args)

    def _convert_url_type(
        self, field_args: dict[str, t.Any], **extra: t.Any
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils URLType to StringField with URL validation."""
        field_args["validators"].append(validators.URL())
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    def _convert_ip_address_type(
        self, field_args: dict[str, t.Any], **extra: t.Any
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils IPAddressType to StringField with IP validation."""
        field_args["validators"].append(validators.IPAddress())
        return fields.StringField(**field_args)

    def _convert_color_type(
        self, field_args: dict[str, t.Any], **extra: t.Any
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils ColorType to StringField with color validation."""
        field_args["validators"].append(valid_color)
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    def _convert_currency_type(
        self, field_args: dict[str, t.Any], **extra: t.Any
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils CurrencyType
        to StringField with currency validation."""
        field_args["validators"].append(valid_currency)
        field_args["filters"] = [avoid_empty_strings]
        return fields.StringField(**field_args)

    def _convert_timezone_type(
        self, column: Any, field_args: dict, **extra
    ) -> fields.StringField:
        """Convert SQLAlchemy-utils TimezoneType
        to StringField with timezone validation."""
        coerce_function = getattr(column.type, "_coerce", None) if column.type else None
        field_args["validators"].append(
            TimeZoneValidator(coerce_function=coerce_function)
        )
        return fields.StringField(**field_args)

    def _convert_choice_type(
        self, column: Any, field_args: dict, **extra
    ) -> fields.SelectField:
        """Convert SQLAlchemy-utils ChoiceType to SelectField with choices."""
        available_choices = []

        if not column.type or not hasattr(column.type, "choices"):
            return fields.StringField(**field_args)

        # Choices can either be specified as an enum, or as a list of tuples
        if isinstance(column.type.choices, EnumMeta):
            available_choices = [(f.value, f.name) for f in column.type.choices]
        else:
            available_choices = column.type.choices

        accepted_values = [
            choice[0] if isinstance(choice, tuple) else choice.value
            for choice in available_choices
        ]

        if column.nullable:
            field_args["allow_blank"] = column.nullable
            accepted_values.append(None)

        field_args["choices"] = available_choices

        # Handle python_type attribute (may not exist on mock objects)
        try:
            field_args["coerce"] = column.type.python_type
        except AttributeError:
            # Fallback to str if python_type is not available
            field_args["coerce"] = str

        return form.Select2Field(**field_args)

    def _convert_arrow_type(
        self, field_args: dict[str, t.Any], **extra: t.Any
    ) -> form.DateTimeField:
        """Convert SQLAlchemy-utils ArrowType to DateTimeField."""
        return form.DateTimeField(**field_args)


# For backward compatibility, create a
# no-op mixin when sqlalchemy-utils is not available
if not SQLALCHEMY_UTILS_AVAILABLE:

    class SQLAlchemyExtendedMixin:
        """No-op mixin when sqlalchemy-utils is not available."""

        def handle_extended_types(
            self, model: Any, column: Any, field_args: dict, **extra
        ) -> None:
            """Return None when sqlalchemy-utils is not available."""
            return None
