Flask-AdminEx
=============

Contributors
------------

-  `Serge S. Koval <https://github.com/MrJoes/>`_

Introduction
------------

This is library for building adminstrative interface on top of Flask framework.

Instead of providing simple scaffolding of the SQLAlchemy models, Flask-AdminEx
provides tools that can be used to build adminstrative interface of any complexity,
using consistent look and feel.

Small example (Flask initialization omitted)::

    app = Flask(__name__)

    admin = Admin()
    admin.add_view(ModelView(User, db.session))
    admin.add_view(GalleryManager(name='Photos', category='Cats'))
    admin.setup_app(app)


Documentation
-------------

Flask-AdminEx is extensively documented, you can find documentation `here <http://readthedocs.org/docs/flask-adminex>`_.

3rd Party Stuff
---------------

Flask-AdminEx is built with help of `Twitter Bootstrap <http://twitter.github.com/bootstrap/>`_ and `Chosen <http://harvesthq.github.com/chosen/>`_.

Kudos
-----

Some ideas were taken from the `Flask-Admin <https://github.com/wilsaj/flask-admin>`_ by Andy Wilson.

Examples
--------

Library comes with three examples, you can find them in `examples` directory.
