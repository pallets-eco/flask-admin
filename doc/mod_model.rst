``flask.ext.adminex.model``
===========================

.. automodule:: flask.ext.adminex.model

    .. autoclass:: BaseModelView

    Permissions
    -----------

    .. autoattribute:: BaseModelView.can_create
    .. autoattribute:: BaseModelView.can_edit
    .. autoattribute:: BaseModelView.can_delete

    Templates
    ---------

    .. autoattribute:: BaseModelView.list_template
    .. autoattribute:: BaseModelView.edit_template
    .. autoattribute:: BaseModelView.create_template

    Customizations
    --------------

    .. autoattribute:: BaseModelView.list_columns
    .. autoattribute:: BaseModelView.excluded_list_columns
    .. autoattribute:: BaseModelView.rename_columns

    .. autoattribute:: BaseModelView.sortable_columns

    .. autoattribute:: BaseModelView.searchable_columns

    .. autoattribute:: BaseModelView.column_filters

    .. autoattribute:: BaseModelView.form_columns
    .. autoattribute:: BaseModelView.excluded_form_columns
    .. autoattribute:: BaseModelView.form_args

    .. autoattribute:: BaseModelView.page_size

    Constructor
    -----------

    .. automethod:: BaseModelView.__init__

    Scaffolding
    -----------

    .. automethod:: BaseModelView.scaffold_pk
    .. automethod:: BaseModelView.scaffold_list_columns
    .. automethod:: BaseModelView.scaffold_sortable_columns
    .. automethod:: BaseModelView.scaffold_form
    .. automethod:: BaseModelView.scaffold_filters

    Configuration
    -------------

    .. automethod:: BaseModelView.get_list_columns
    .. automethod:: BaseModelView.get_sortable_columns

    .. automethod:: BaseModelView.get_create_form
    .. automethod:: BaseModelView.get_edit_form

    .. automethod:: BaseModelView.init_search

    .. automethod:: BaseModelView.get_filters
    .. automethod:: BaseModelView.is_valid_filter

    Data
    ----

    .. automethod:: BaseModelView.get_list
    .. automethod:: BaseModelView.get_one

    .. automethod:: BaseModelView.create_model
    .. automethod:: BaseModelView.update_model
    .. automethod:: BaseModelView.delete_model

    Helpers
    -------

    .. automethod:: BaseModelView.create_form
    .. automethod:: BaseModelView.edit_form
    .. automethod:: BaseModelView.is_sortable
    .. automethod:: BaseModelView.prettify_name

    Views
    -----

    .. automethod:: BaseModelView.index_view
    .. automethod:: BaseModelView.create_view
    .. automethod:: BaseModelView.edit_view
    .. automethod:: BaseModelView.delete_view

    Internal API
    ------------

    .. automethod:: BaseModelView._get_url
