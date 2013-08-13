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

Models with multiple primary keys have limited support, as a few pitfalls are waiting for you.
With using multiple primary keys, weak entities can be used with Flask-Admin.

Lets Model a car with it's tyres::

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

To be able to CRUD the ``Tyre`` class, two steps are necessary, when definig the AdminView::

    class TyreAdmin(sqla.ModelView):
        form_columns = ['car', 'tyre_id', 'desc']
        form_excluded_pk_columns_from_unique_validation = ('car_id', 'tyre_id')

The ``form_columns`` needs to be explizit, as per default only one primary key is displayed. When, like in this
example, one part of the key is a foreign key, do not include the foreign-key-columns here, but the
coresponding relationship.

Per default, all pimary-key-columns are validated for uniquenes. As describe in :doc:`api/mod_model`
the ``form_excluded_pk_columns_from_unique_validation`` attribute can, and must, be used, to exclude *all*
primary-key-columns from this check. Your database will tell you via ``Sqlalchemy``, if the operation
was successfull or not. (Watch out for IntegrityErrors).

A standalone script with the Examples from above can be found in the examples directory.

Example
-------

Flask-Admin comes with relatively advanced example, which you can
see `here <https://github.com/mrjoes/flask-admin/tree/master/examples/sqla>`_.
