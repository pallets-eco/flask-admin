``flask_admin.contrib.sqlmodel``
=================================

SQLModel model backend implementation.

This module provides Flask-Admin integration for SQLModel with support for:

* **Core SQLModel types**: Native Python types (str, int, float, bool) and Pydantic field types
* **Pydantic constrained types**: constr, conint, confloat with proper validation
* **Property and computed field support**: Auto-detection of properties with setters and post-query filtering
* **Field class overrides**: Custom WTForms field classes via view-level ``form_overrides``
* **UUID field support**: Native SQLModel UUID primary keys with proper form handling
* **SQLAlchemy-utils extended types**: Optional support via :mod:`~flask_admin.contrib.sqlmodel.mixins`

.. automodule:: flask_admin.contrib.sqlmodel

Usage Examples
--------------

**Field Class Overrides**

To use custom WTForms field classes, use view-level ``form_overrides``:

.. code-block:: python

    from wtforms import TextAreaField
    from flask_admin.contrib.sqlmodel import SQLModelView

    class PostAdmin(SQLModelView):
        form_overrides = {
            'description': TextAreaField,  # Use TextArea instead of StringField
        }

**Property and Computed Fields**

Properties with both getter and setter are automatically supported for display and filtering:

.. code-block:: python

    from sqlmodel import SQLModel, Field

    class User(SQLModel, table=True):
        first_name: str
        last_name: str

        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

        @full_name.setter
        def full_name(self, value: str):
            # Setter required for Flask-Admin detection
            pass

    class UserAdmin(SQLModelView):
        column_list = ['first_name', 'last_name', 'full_name']
        column_filters = ['full_name']

**UUID Primary Keys**

Native SQLModel UUID primary keys are fully supported:

.. code-block:: python

    import uuid
    from sqlmodel import SQLModel, Field

    class Article(SQLModel, table=True):
        id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
        title: str

API Reference
-------------

.. autoclass:: SQLModelView
        :members:
        :inherited-members:
        :exclude-members: column_filters, filter_converter, model_form_converter,
                          inline_model_form_converter, fast_mass_delete,
                          inline_models, form_choices,
                          column_type_formatters

        Class inherits configuration options from :class:`~flask_admin.model.BaseModelView` and they're not displayed here.

        .. autoattribute:: column_filters
        .. autoattribute:: filter_converter
        .. autoattribute:: model_form_converter
        .. autoattribute:: inline_model_form_converter
        .. autoattribute:: fast_mass_delete
        .. autoattribute:: inline_models
        .. autoattribute:: form_choices
        .. autoattribute:: column_type_formatters
