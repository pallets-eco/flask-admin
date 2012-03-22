``flask.ext.adminex.base``
==========================

.. automodule:: flask.ext.adminex.base

    Base View
    ---------

    .. autofunction:: expose

    .. autoclass:: BaseView

    .. automethod:: BaseView.__init__
    .. automethod:: BaseView.is_accessible
    .. automethod:: BaseView.render

    Internal
    --------

    .. automethod:: BaseView.create_blueprint


    Default view
    ------------

    .. autoclass:: AdminIndexView

        .. automethod:: __init__

    Admin
    -----

    .. autoclass:: Admin

        .. automethod:: __init__
        .. automethod:: add_view
        .. automethod:: init_app
        .. automethod:: menu
