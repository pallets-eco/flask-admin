``flask.ext.adminex.ext.sqlamodel``
===================================

.. automodule:: flask.ext.adminex.ext.sqlamodel

    .. autoclass:: ModelView

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

    .. autoattribute:: ModelView.searchable_columns

    .. autoattribute:: BaseModelView.form_columns
    .. autoattribute:: BaseModelView.excluded_form_columns
    .. autoattribute:: BaseModelView.form_args

    .. autoattribute:: BaseModelView.page_size

    SQLAlchemy-related Customizations
    ---------------------------------
    .. autoattribute:: ModelView.hide_backrefs

    .. autoattribute:: ModelView.auto_select_related
    .. autoattribute:: ModelView.list_select_related

    Constructor
    -----------

    .. automethod:: ModelView.__init__

    Scaffolding
    -----------

    .. automethod:: ModelView.scaffold_list_columns
    .. automethod:: ModelView.scaffold_sortable_columns
    .. automethod:: ModelView.scaffold_form

    Configuration
    -------------

    .. automethod:: ModelView.get_list_columns
    .. automethod:: ModelView.get_sortable_columns

    .. automethod:: ModelView.get_create_form
    .. automethod:: ModelView.get_edit_form

    .. automethod:: ModelView.init_search

    Data
    ----

    .. automethod:: ModelView.get_list
    .. automethod:: ModelView.get_one

    .. automethod:: ModelView.create_model
    .. automethod:: ModelView.update_model
    .. automethod:: ModelView.delete_model

    Helpers
    -------

    .. automethod:: ModelView.create_form
    .. automethod:: ModelView.edit_form
    .. automethod:: ModelView.is_sortable
    .. automethod:: ModelView.prettify_name

    Views
    -----

    .. automethod:: ModelView.index_view
    .. automethod:: ModelView.create_view
    .. automethod:: ModelView.edit_view
    .. automethod:: ModelView.delete_view

    Internal API
    ------------

    .. automethod:: ModelView._get_url
    .. automethod:: ModelView.scaffold_auto_joins
    .. automethod:: ModelView.is_text_column_type
