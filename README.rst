Flask-Admin
===========

Introduction
------------

This is library for building adminstrative interface on top of Flask framework.

Instead of providing simple scaffolding for the SQLAlchemy models, Flask-Admin
provides tools that can be used to build adminstrative interface of any complexity,
using consistent look and feel.

Small example (Flask initialization omitted)::

    app = Flask(__name__)

    admin = Admin()
    admin.add_view(ModelView(User, db.session))
    admin.add_view(GalleryManager(name='Photos', category='Cats'))
    admin.init_app(app)

If you're looking for 0.x version of the Flask-Admin written by Andy Wilson, check `here <http://github.com/wilsaj/flask-admin-old>`_.

Documentation
-------------

Flask-Admin is extensively documented, you can find `documentation here <http://readthedocs.org/docs/flask-admin>`_.

3rd Party Stuff
---------------

Flask-Admin is built with help of `Twitter Bootstrap <http://twitter.github.com/bootstrap/>`_ and `Chosen <http://harvesthq.github.com/chosen/>`_.

Kudos
-----

Some ideas were taken from the `Flask-Admin <https://github.com/wilsaj/flask-admin-old>`_ by Andy Wilson.

Examples
--------

Library comes with few examples, you can find them in `examples` directory.
