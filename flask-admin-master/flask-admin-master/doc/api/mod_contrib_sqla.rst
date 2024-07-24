``flask_admin.contrib.sqla``
============================

SQLAlchemy model backend implementation.

.. automodule:: flask_admin.contrib.sqla

    .. autoclass:: ModelView
        :members:
        :inherited-members:
        :exclude-members: column_auto_select_related,
                          column_select_related_list, column_searchable_list,
                          column_filters, filter_converter, model_form_converter,
                          inline_model_form_converter, fast_mass_delete,
                          inline_models, form_choices,
                          form_optional_types

        Class inherits configuration options from :class:`~flask_admin.model.BaseModelView` and they're not displayed here.

        .. autoattribute:: column_auto_select_related
        .. autoattribute:: column_select_related_list
        .. autoattribute:: column_searchable_list
        .. autoattribute:: column_filters
        .. autoattribute:: filter_converter
        .. autoattribute:: model_form_converter
        .. autoattribute:: inline_model_form_converter
        .. autoattribute:: fast_mass_delete
        .. autoattribute:: inline_models
        .. autoattribute:: form_choices
        .. autoattribute:: form_optional_types
