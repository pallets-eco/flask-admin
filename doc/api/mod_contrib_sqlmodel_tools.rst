``flask_admin.contrib.sqlmodel.tools``
=====================================

Utility functions and data structures for SQLModel introspection and analysis.

.. automodule:: flask_admin.contrib.sqlmodel.tools

    Data Structures
    ---------------

    .. autoclass:: ModelField
        :members:

        Enhanced dataclass for storing SQLModel field metadata, including support
        for field class overrides and property/computed field detection.

    Utility Functions
    -----------------

    .. autofunction:: get_primary_key

    .. autofunction:: has_multiple_pks

    .. autofunction:: get_primary_key_types

        Returns the Python types of all primary key columns for a SQLModel.

    .. autofunction:: convert_pk_value

        Converts a primary key value to the appropriate Python type based on 
        column type information.

    .. autofunction:: convert_pk_from_url

        Converts primary key values from URL parameters to appropriate Python types
        for use in database queries.

    .. autofunction:: is_relationship

    .. autofunction:: is_association_proxy

    .. autofunction:: is_hybrid_property

    .. autofunction:: is_computed_field

        Detects if a field name corresponds to a computed field (property) in a SQLModel.

    .. autofunction:: is_property_with_setter

        Checks if a model attribute is a property with both getter and setter methods.

    .. autofunction:: get_field_with_path

    .. autofunction:: get_query_for_ids

    .. autofunction:: parse_like_term

    .. autofunction:: iterdecode

    .. autofunction:: iterencode

    .. autofunction:: resolve_model

    Type Checking Functions
    -----------------------

    .. autofunction:: is_sqlmodel

    .. autofunction:: is_optional_type

    .. autofunction:: get_optional_inner_type

    .. autofunction:: extract_type_from_optional

    .. autofunction:: is_union_type

    .. autofunction:: get_union_args

    Model Introspection
    -------------------

    .. autofunction:: get_relationships

    .. autofunction:: get_columns_for_field

    .. autofunction:: get_type

    .. autofunction:: get_column_type