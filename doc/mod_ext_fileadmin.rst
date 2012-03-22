``flask.ext.adminex.ext.fileadmin``
===================================

.. automodule:: flask.ext.adminex.ext.fileadmin

    .. autoclass:: FileAdmin

    Permissions
    -----------

    .. autoattribute:: FileAdmin.can_upload
    .. autoattribute:: FileAdmin.can_delete
    .. autoattribute:: FileAdmin.can_delete_dirs
    .. autoattribute:: FileAdmin.can_mkdir
    .. autoattribute:: FileAdmin.can_rename
    .. autoattribute:: FileAdmin.allowed_extensions

    Templates
    ---------

    .. autoattribute:: FileAdmin.list_template
    .. autoattribute:: FileAdmin.upload_template
    .. autoattribute:: FileAdmin.mkdir_template
    .. autoattribute:: FileAdmin.rename_template

    Constructor
    -----------

    .. automethod:: FileAdmin.__init__

    Permissions
    -----------

    .. automethod:: FileAdmin.is_accessible_path
    .. automethod:: FileAdmin.is_file_allowed

    Helpers
    -------

    .. automethod:: FileAdmin.get_base_path
    .. automethod:: FileAdmin.get_base_url
    .. automethod:: FileAdmin.is_in_folder
    .. automethod:: FileAdmin.save_file

    Views
    -----

    .. automethod:: FileAdmin.index
    .. automethod:: FileAdmin.upload
    .. automethod:: FileAdmin.mkdir
    .. automethod:: FileAdmin.delete
    .. automethod:: FileAdmin.rename

    Internal API
    ------------

    .. automethod:: FileAdmin._get_dir_url
    .. automethod:: FileAdmin._get_file_url
    .. automethod:: FileAdmin._normalize_path

