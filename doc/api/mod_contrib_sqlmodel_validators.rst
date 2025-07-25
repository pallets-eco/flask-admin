``flask_admin.contrib.sqlmodel.validators``
===========================================

SQLModel validators for Flask-Admin forms.

.. automodule:: flask_admin.contrib.sqlmodel.validators

    .. autoclass:: Unique
        :members:

        Validates field value uniqueness against specified SQLModel table field.

    .. autoclass:: ItemsRequired
        :members:

        A version of ``InputRequired`` validator that works with relations,
        requiring a minimum number of related items.

.. note::

    **SQLAlchemy-utils specific validators have been moved** to the 
    :mod:`flask_admin.contrib.sqlmodel.mixins` module for better 
    dependency management:

    * ``valid_color`` - Color validation
    * ``valid_currency`` - Currency code validation  
    * ``TimeZoneValidator`` - Timezone validation

    These validators are now part of the ``SQLAlchemyExtendedMixin`` class
    and are only available when the ``sqlalchemy-utils`` package is installed.