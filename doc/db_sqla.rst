SQLAlchemy backend
==================

Flask-Admin comes with SQLAlchemy ORM backend.

Notable features:

 - SQLAlchemy 0.6+ support;
 - Paging, sorting, filters;
 - Proper model relationship handling;
 - Inline editing of related models.

Getting Started
---------------

In order to use SQLAlchemy model scaffolding, you need to have:

 1. SQLAlchemy ORM `model <http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html#declare-a-mapping>`_
 2. Initialized database `session <http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html#creating-a-session>`_

If you use Flask-SQLAlchemy, this is how you initialize Flask-Admin
and get session from the `SQLAlchemy` object::

    from flask import Flask
    from flask.ext.sqlalchemy import SQLAlchemy
    from flask.ext.admin import Admin
    from flask.ext.admin.contrib.sqla import ModelView

    app = Flask(__name__)
    # .. read settings
    db = SQLAlchemy(app)

    # .. model declarations here

    if __name__ == '__main__':
        admin = Admin(app)
        # .. add ModelViews
        # admin.add_view(ModelView(SomeModel, db.session))

Creating simple model
---------------------

Using previous template, lets create simple model::

    # .. flask initialization
    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), unique=True)
        email = db.Column(db.String(128))

    if __name__ == '__main__':
        admin = Admin(app)
        admin.add_view(ModelView(User, db.session))

        db.create_all()
        app.run('0.0.0.0', 8000)

If you will run this example and open `http://localhost:8000/ <http://localhost:8000/>`_,
you will see that Flask-Admin generated administrative page for the
model:

    .. image:: images/sqla/sqla_1.png
        :width: 640
        :target: ../_images/sqla_1.png

You can add new models, edit existing, etc.

Customizing administrative interface
------------------------------------

List view can be customized in different ways.

First of all, you can use various class-level properties to configure
what should be displayed and how. For example, :attr:`~flask.ext.admin.contrib.sqla.ModelView.column_list` can be used to show some of
the column or include extra columns from related models.

For example::

    class UserView(ModelView):
        # Show only name and email columns in list view
        column_list = ('name', 'email')

        # Enable search functionality - it will search for terms in
        # name and email fields
        column_searchable_list = ('name', 'email')

        # Add filters for name and email columns
        column_filters = ('name', 'email')

Alternatively, you can override some of the :class:`~flask.ext.admin.contrib.sqla.ModelView` methods and implement your custom logic.

For example, if you need to contribute additional field to the generated form,
you can do something like this::

    class UserView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = TextField('Extra')
            return form_class

Check :doc:`api/mod_contrib_sqla` documentation for list of
configuration properties and methods.

Multiple Primary Keys
---------------------

Flask-Admin has limited support for models with multiple primary keys. It only covers specific case when
all but one primary keys are foreign keys to another model. For example, model inheritance following
this convention.

Lets Model a car with its tyres::

    class Car(db.Model):
        __tablename__ = 'cars'
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        desc = db.Column(db.String(50))

        def __unicode__(self):
            return self.desc

    class Tyre(db.Model):
        __tablename__ = 'tyres'
        car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), primary_key=True)
        tyre_id = db.Column(db.Integer, primary_key=True)
        car = db.relationship('Car', backref='tyres')
        desc = db.Column(db.String(50))

A specific tyre is identified by using the two primary key columns of the ``Tyre`` class, of which the ``car_id`` key
is itself a foreign key to the class ``Car``.

To be able to CRUD the ``Tyre`` class, you need to enumerate columns when defining the AdminView::

    class TyreAdmin(sqla.ModelView):
        form_columns = ['car', 'tyre_id', 'desc']

The ``form_columns`` needs to be explicit, as per default only one primary key is displayed.

When having multiple primary keys, **no** validation for uniqueness *prior* to saving of the object will be done. Saving
a model that violates a unique-constraint leads to an Sqlalchemy-Integrity-Error. In this case, ``Flask-Admin`` displays
a proper error message and you can change the data in the form. When the application has been started with ``debug=True``
the ``werkzeug`` debugger will catch the exception and will display the stacktrace.

A standalone script with the Examples from above can be found in the examples directory.

Example
-------

Flask-Admin comes with relatively advanced example, which you can
see `here <https://github.com/mrjoes/flask-admin/tree/master/examples/sqla>`_.
