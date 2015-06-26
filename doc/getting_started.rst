Getting Started
===========

Flask-Admin lets you build complicated interfaces by grouping individual views
together in classes. So each view that you see from the frontend, represents a
method on a class that has explicitly been added to the interface.

These view classes are especially helpful when they are tied to particular
database models,
because they let you group together all of the usual
**Create, Read, Update, Delete** (CRUD) view logic into a single, self-contained
class for each of your models.

Initialization
--------------

The first step, is to initialise an empty admin interface on your Flask app::

    from flask import Flask
    from flask_admin import Admin

    app = Flask(__name__)

    admin = Admin(app, name='My App')
    # Add administrative views here

    app.run()

Here, the *name* parameter is optional. If you start this application and navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see an empty "Home" page with a navigation bar on top, and the *name* that you specified.

.. note::

    As an alternative to passing a Flask application object to the Admin constructor, you can also call the
    :meth:`~flask_admin.base.Admin.init_app` function, after the Admin instance has been initialized::

        admin = Admin(name='My App')
        # Add views here
        admin.init_app(app)

Adding Model Views
-----------

Model views allow you to add dedicated admin pages for each of the models in your database. Do this by creating
instances of the *ModelView* class, which you can import from one of Flask-Admin's built-in ORM backends. An example
is the SQLAlchemy backend, which you can use as follows::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    admin = Admin(app)
    admin.add_view(ModelView(User, db.session))

Straight out of the box, this gives you a set of fully featured *CRUD* views for your model:

    * A list view, with support for searching, sorting and filtering
    * a view for adding new records
    * a view for editing existing records
    * the ability to delete records.

There are many options available for customizing the display and functionality of these builtin view.
For more details on that, see :ref:`customising-builtin-views`.

Overriding the index page
-------------------------

