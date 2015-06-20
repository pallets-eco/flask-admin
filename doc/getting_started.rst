Getting started
===========

Initialization
--------------

To start using Flask-Admin, you have to create a :class:`~flask_admin.base.Admin` class instance and associate it
with the Flask
application instance::

    from flask import Flask
    from flask_admin import Admin

    app = Flask(__name__)

    admin = Admin(app)
    # Add administrative views here

    app.run()

If you start this application and navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see an empty "Home" page with a navigation bar on top

    .. image:: images/quickstart/quickstart_1.png
        :target: ../_images/quickstart_1.png

You can change the application name by passing a value for the *name* parameter to the
:class:`~flask_admin.base.Admin` class constructor::

    admin = Admin(app, name='My App')

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

This creates an admin page for the *User* model. By default, the list view looks like

    .. image:: images/quickstart/quickstart_4.png
        :width: 640
        :target: ../_images/quickstart_4.png

To customize these model views, you have two options: Either you can override the public properties of the *ModelView*
class, or you can override its methods.

For example, if you want to disable model creation and only show certain columns in the list view, you can do
something like::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class MyView(ModelView):
        # Disable model creation
        can_create = False

        # Override displayed fields
        column_list = ('login', 'email')

        def __init__(self, session, **kwargs):
            # You can pass name and other parameters if you want to
            super(MyView, self).__init__(User, session, **kwargs)

    admin = Admin(app)
    admin.add_view(MyView(db.session))

Overriding form elements can be a bit trickier, but it is still possible. Here's an example of
how to set up a form that includes a column named *status* that allows only predefined values and
therefore should use a *SelectField*::

    from wtforms.fields import SelectField

    class MyView(ModelView):
        form_overrides = dict(status=SelectField)
        form_args = dict(
            # Pass the choices to the `SelectField`
            status=dict(
                choices=[(0, 'waiting'), (1, 'in_progress'), (2, 'finished')]
            ))


It is relatively easy to add support for different database backends (Mongo, etc) by inheriting from
:class:`~flask_admin.model.BaseModelView`.
class and implementing database-related methods.

Please refer to :mod:`flask_admin.contrib.sqla` documentation on how to customize the behavior of model-based
administrative views.

Overriding the index page
-------------------------

