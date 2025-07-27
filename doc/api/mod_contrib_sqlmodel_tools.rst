``flask_admin.contrib.sqlmodel.tools``
======================================

Utility functions and data structures for SQLModel introspection and analysis.

.. automodule:: flask_admin.contrib.sqlmodel.tools

    Data Structures
    ---------------

    .. autoclass:: ModelField
        :members:

        Enhanced dataclass for storing SQLModel field metadata, including support
        for field class overrides and property/computed field detection.

    Core Utility Functions
    ----------------------

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

    .. autofunction:: get_query_for_ids

    .. autofunction:: parse_like_term

    .. autofunction:: iterdecode

    .. autofunction:: iterencode

    .. autofunction:: resolve_model

    Model Field Analysis
    --------------------

    .. autofunction:: get_model_fields

        Get all fields from a model, supporting both SQLModel and SQLAlchemy.
        For SQLModel, includes regular fields, properties, and computed fields.

    .. autofunction:: get_wtform_compatible_fields

        Get fields that are compatible with WTForms.
        This includes regular fields and properties/computed fields with setters.

    .. autofunction:: get_readonly_fields

        Get fields that are read-only (computed fields and properties without setters).

    .. autofunction:: get_sqlmodel_fields

        Get all fields from a SQLModel, including both regular fields and computed fields.

    .. autofunction:: get_sqlmodel_column_names

        Get column names from SQLModel table.

    .. autofunction:: get_sqlmodel_field_names

        Get field names from a SQLModel class (works for both table and non-table models).

    .. autofunction:: get_all_model_fields

        Universal function to get all fields from any model type.
        Works with SQLModel (table and non-table) and SQLAlchemy models.

    Type Checking Functions
    -----------------------

    .. autofunction:: is_sqlmodel_class

        Check if a model is a SQLModel class.

    .. autofunction:: is_sqlmodel_table_model

        Check if model is a SQLModel with table=True.

    .. autofunction:: is_sqlmodel_table

        Check if the model is a SQLModel table (has table=True).
        Alias for is_sqlmodel_table_model() for cleaner naming.

    Pydantic Type Support
    ---------------------

    .. autofunction:: is_pydantic_constrained_type

        Check if type is a Pydantic constrained type (Pydantic v2).

    .. autofunction:: get_pydantic_field_constraints

        Extract Pydantic field constraints for WTForms validation.

    Relationship and Property Analysis
    ----------------------------------

    .. autofunction:: is_relationship

    .. autofunction:: is_association_proxy

    .. autofunction:: is_hybrid_property

    .. autofunction:: is_computed_field

        Detects if a field name corresponds to a computed field (property) in a SQLModel.

    .. autofunction:: is_sqlmodel_property

        Check if attribute is a @property in SQLModel.

    .. autofunction:: get_computed_fields

        Get computed fields from SQLModel.
        SQLModel uses Pydantic's computed_field instead of SQLAlchemy's hybrid_property.

    .. autofunction:: get_sqlmodel_properties

        Get all @property decorated methods from a SQLModel class.

    .. autofunction:: get_hybrid_properties

        Get hybrid properties from a model.
        Works with both SQLModel and SQLAlchemy models.

    Query and Database Operations
    -----------------------------

    .. autofunction:: get_field_with_path

    .. autofunction:: get_columns_for_field

        Get columns for a field, handling both SQLModel and SQLAlchemy fields.

    .. autofunction:: need_join

        Check if join to a table is necessary.
        Works with both SQLModel and SQLAlchemy models.

    .. autofunction:: get_model_table

        Get the table from a model, handling both SQLModel and SQLAlchemy.

    .. autofunction:: filter_foreign_columns

        Return list of columns that belong to passed table.

    .. autofunction:: tuple_operator_in

        The ``tuple_`` Operator only works on certain engines like MySQL or Postgresql.
        It does not work with sqlite.

    WTForms Integration
    -------------------

    .. autofunction:: create_property_setter

        Create a setter method for a computed field or property to make it WTForms compatible.

    .. autofunction:: make_computed_field_wtforms_compatible

        Add a setter method to a computed field to make it WTForms compatible.

    .. autofunction:: get_field_value_with_fallback

        Get field value with fallback to private WTForms storage.

    .. autofunction:: set_field_value_with_fallback

        Set field value with fallback to private WTForms storage.

    Field Type Utilities
    --------------------

    .. autofunction:: get_field_python_type

        Get the Python type for a field, handling Optional, Union, and special Pydantic types.

    .. autofunction:: is_field_optional

        Check if a field is optional (can be None).

    .. autofunction:: get_field_constraints

        Extract constraints from a field for validation.

    .. autofunction:: validate_field_type

        Validate a value against a field's type constraints.

    Debugging and Introspection
    ---------------------------

    .. autofunction:: debug_model_fields

        Generate a debug string showing all fields and their properties.

    .. autofunction:: get_model_field_summary

        Get a summary of all fields in a model.
