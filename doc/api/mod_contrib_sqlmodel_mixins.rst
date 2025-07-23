``flask_admin.contrib.sqlmodel.mixins``
========================================

SQLAlchemy-utils extended types support mixin for SQLModel forms.

This module provides optional support for SQLAlchemy-utils extended field types
through a mixin architecture. The ``AdminModelConverter`` in the form module
inherits from ``SQLAlchemyExtendedMixin`` to provide seamless integration.

.. automodule:: flask_admin.contrib.sqlmodel.mixins

    .. autoclass:: SQLAlchemyExtendedMixin
        :members:
        :show-inheritance:

        This mixin provides optional support for SQLAlchemy-utils extended field types.
        It gracefully degrades when the ``sqlalchemy-utils`` package is not available.

        **Supported Extended Types:**

        * **EmailType**: Email validation with proper WTForms Email validator
        * **URLType**: URL validation with WTForms URL validator  
        * **IPAddressType**: IP address validation
        * **ColorType**: Color validation (hex codes and named colors)
        * **CurrencyType**: ISO currency code validation
        * **TimezoneType**: Timezone validation with pytz support
        * **ChoiceType**: Choice enumeration fields (supports Enum and tuples)
        * **ArrowType**: Arrow datetime fields

        **Graceful Degradation:**
        
        When ``sqlalchemy-utils`` is not installed, all methods return ``None``,
        allowing the main form converter to handle fields as regular SQLAlchemy types.

    .. autofunction:: valid_color

        Validates color values. Accepts:
        
        * Hex color codes: ``#FF0000``, ``#fff``
        * Named CSS colors: ``red``, ``blue``, ``green``, etc.

    .. autofunction:: valid_currency

        Validates ISO 4217 currency codes (e.g., ``USD``, ``EUR``, ``GBP``).

    .. autoclass:: TimeZoneValidator
        :members:

        Validates timezone strings using the provided coerce function or pytz fallback.

    .. autofunction:: avoid_empty_strings

        Utility function that converts empty strings and whitespace to None.