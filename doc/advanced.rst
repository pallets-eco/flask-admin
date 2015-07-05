Advanced Functionality
=================================

.. _extending-builtin-templates:

Extending the Builtin Templates
---------------------------------

****

By default, Flask-Admin uses three pre-defined templates for displaying your models in the admin-interface:

* `admin/model/list.html`
* `admin/model/create.html`
* `admin/model/edit.html`

All three of these extend the `admin/master.html` template, and you can override them by defining your own templates,
with the same path relative to your `templates` folder.

You could also choose to extend these templates, rather than overriding them. In this case you will need to
point your classes at your own templates, rather than letting them use the defaults. For example, your own template
for the *edit* views could be defined in `templates/my_edit_template.html` to look something like::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
        {{ super() }}
        ...
    {% endblock %}

And your classes could be made to use this template by setting the appropriate class property::

    class MyModelView(ModelView):
        edit_template = 'my_edit_template.html'

The three available properties are simply called `list_template`, `create_template` and `edit_template`.

If you want to use your own base template, then pass the name of the template to
the admin constructor during initialization::

    admin = Admin(app, base_template='my_master.html')

Available Template Blocks
****************************

Flask-Admin defines one *base* template at `admin/master.html` that all the other admin templates are derived
from. This template is a proxy which points to `admin/base.html`, which defines
the following blocks:

============== ========================================================================
Block Name     Description
============== ========================================================================
head_meta      Page metadata in the header
title          Page title
head_css       Various CSS includes in the header
head           Empty block in HTML head, in case you want to put something  there
page_body      Page layout
brand          Logo in the menu bar
main_menu      Main menu
menu_links     Links menu
access_control Section to the right of the menu (can be used to add login/logout buttons)
messages       Alerts and various messages
body           Content (that's where your view will be displayed)
tail           Empty area below content
============== ========================================================================

In addition to all of the blocks that are inherited from `admin/master.html`, the `admin/model/list.html` template
also contains the following blocks:

======================= ============================================
Block Name              Description
======================= ============================================
model_menu_bar          Menu bar
model_list_table  		Table container
list_header       		Table header row
list_row_actions_header Actions header
list_row                Single row
list_row_actions        Row action cell with edit/remove/etc buttons
empty_list_message      Message that will be displayed if there are no models found
======================= ============================================

Replacing Individual Form Fields
------------------------------------------

****

The `form_overrides` attribute allows you to replace individual fields within a form.
A common use-case for this would be to add a rich text editor, or to handle
file / image uploads that need to be tied to a field in your model.

Rich-Text Fields
**********************
To handle complicated text content, use a *WYSIWIG* text editor, like
`CKEditor <http://ckeditor.com/>`_ by subclassing some of the builtin WTForms
classes as follows::

    from wtforms import TextAreaField
    from wtforms.widgets import TextArea

    class CKTextAreaWidget(TextArea):
        def __call__(self, field, **kwargs):
            if kwargs.get('class'):
                kwargs['class'] += ' ckeditor'
            else:
                kwargs.setdefault('class', 'ckeditor')
            return super(CKTextAreaWidget, self).__call__(field, **kwargs)

    class CKTextAreaField(TextAreaField):
        widget = CKTextAreaWidget()

    class MessageAdmin(ModelView):
        form_overrides = {
            'body': CKTextAreaField
        }
        create_template = 'ckeditor.html'
        edit_template = 'ckeditor.html'

For this to work, you would also need to create a template that extends the default
functionality by including the necessary CKEditor javascript on the `create` and
`edit` pages. Save this in `templates/ckeditor.html`::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
      {{ super() }}
      <script src="http://cdnjs.cloudflare.com/ajax/libs/ckeditor/4.0.1/ckeditor.js"></script>
    {% endblock %}

File & Image Fields
*******************

Flask-Admin comes with a builtin `FileUploadField` and `ImageUploadField`. To make use
of them, you'll need to specify an upload directory, and add them to the forms in question.
Image handling also requires you to have `Pillow <https://pypi.python.org/pypi/Pillow/2.8.2>`_ installed.

Have a look at the example at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/forms.

If you are using the MongoEngine backend, Flask-Admin supports GridFS-backed image- and file uploads, done through WTForms fields. Documentation can be found
at :mod:`flask_admin.contrib.mongoengine.fields`.

If you just want to manage static files in a directory, without tying them to a database model, then
rather use the handy :ref:`File-Admin<file-admin>` plugin.

Localization with Flask-Babelex
------------------------------------------

****

Enabling localization is relatively simple.

#. Install `Flask-BabelEx <http://github.com/mrjoes/flask-babelex/>`_ to do the heavy
   lifting. It's a fork of the
   `Flask-Babel <http://github.com/mitshuhiko/flask-babel/>`_ package::

        pip install flask-babelex

#. Initialize Flask-BabelEx by creating instance of `Babel` class::

        from flask import app
        from flask_babelex import Babel

        app = Flask(__name__)
        babel = Babel(app)

#. Create a locale selector function::

        @babel.localeselector
        def get_locale():
            if request.args.get('lang'):
                session['lang'] = request.args.get('lang')
            return session.get('lang', 'en')

   Now, you could try out a French version of the application at: `http://localhost:5000/admin/?lang=fr <http://localhost:5000/admin/?lang=fr>`_.

Go ahead and add your own logic to the locale selector function. The application could store locale in
a user profile, cookie, session, etc. And it could interrogate the `Accept-Language`
header for making the selection automatically.

If the builtin translations are not enough, look at the `Flask-BabelEx documentation <https://pythonhosted.org/Flask-BabelEx/>`_
to see how you can add your own.

.. _file-admin:

Managing Files & Folders
--------------------------------

****

To manage static files, that are not tied to your db model, Flask-Admin comes with
the FileAdmin plugin. It gives you the ability to upload, delete, rename, etc. You
can use it by adding a FileAdmin view to your app::

    from flask_admin.contrib.fileadmin import FileAdmin

    import os.path as op

    # Flask setup here

    admin = Admin(app)

    path = op.join(op.dirname(__file__), 'static')
    admin.add_view(FileAdmin(path, '/static/', name='Static Files'))

You can disable uploads, disable file deletion, restrict file uploads to certain types, etc.
Check :mod:`flask_admin.contrib.fileadmin` in the API documentation for more details.

Managing geographical models with the GeoAlchemy backend
----------------------------------------------------------------

****

If you want to store spatial information in a GIS database, Flask-Admin has
you covered. The `GeoAlchemy`_ backend extends the SQLAlchemy backend (just as
GeoAlchemy extends SQLAlchemy) to give you a pretty and functional map-based
editor for your admin pages.

Some notable features include:

 - Maps are displayed using the amazing `Leaflet`_ Javascript library,
   with map data from `Mapbox`_.
 - Geographic information, including points, lines and polygons, can be edited
   interactively using `Leaflet.Draw`_.
 - Graceful fallback: `GeoJSON`_ data can be edited in a ``<textarea>``, if the
   user has turned off Javascript.
 - Works with a `Geometry`_ SQL field that is integrated with `Shapely`_ objects.

To get started, define some fields on your model using GeoAlchemy's *Geometry*
field. An then, add model views to your interface using the ModelView class
from the GeoAlchemy backend, rather than the usual SQLAlchemy backend::

    from geoalchemy2 import Geometry
    from flask_admin.contrib.geoa import ModelView

    # .. flask initialization
    db = SQLAlchemy(app)

    class Location(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), unique=True)
        point = db.Column(Geometry("POINT"))

Some of the Geometry field types that are available include:
"POINT", "MULTIPOINT", "POLYGON", "MULTIPOLYGON", "LINESTRING" and "MULTILINESTRING".

Have a look at https://github.com/flask-admin/flask-admin/tree/master/examples/geo_alchemy
to get started.

Loading Tiles From Mapbox
**************************************

To have map data display correctly, you'll have to sign up for a Mapbox account and
include some credentials in your application's config::

    app = Flask(__name__)
    app.config['MAPBOX_MAP_ID'] = "example.abc123"
    app.config['MAPBOX_ACCESS_TOKEN'] = "pk.def456"


Leaflet supports loading map tiles from any arbitrary map tile provider, but
at the moment, Flask-Admin only supports Mapbox. If you want to use other
providers, make a pull request!

Limitations
*******************

There's currently no way to sort, filter, or search on geometric fields
in the admin. It's not clear that there's a good way to do so.
If you have any ideas or suggestions, make a pull request!

Further Reading
*******************

* GeoAlchemy: http://geoalchemy-2.readthedocs.org/
* Leaflet: http://leafletjs.com/
* Leaflet.Draw: https://github.com/Leaflet/Leaflet.draw
* Shapely: http://toblerity.org/shapely/
* Mapbox: https://www.mapbox.com/
* GeoJSON: http://geojson.org/
* Geometry: http://geoalchemy-2.readthedocs.org/en/latest/types.html#geoalchemy2.types.Geometry

Customising builtin forms via form rendering rules
--------------------------------------------------------

****

Before version 1.0.7, all model backends were rendering the *create* and *edit* forms
using a special Jinja2 macro, which was looping over the fields of a WTForms form object and displaying
them one by one. This works well, but it is difficult to customize.

Starting from version 1.0.7, Flask-Admin supports form rendering rules, to give you fine grained control of how
the forms for your modules should be displayed.

The basic idea is pretty simple: the customizable rendering rules replace a static macro, so that you can tell
Flask-Admin how each form should be rendered. As an extension, however, the rendering rules also let you do a
bit more: You can use them to output HTML, call Jinja2 macros, render fields and so on.

Essentially, form rendering rules abstract the rendering, so that it becomes separate from the form definition. So,
for example, it no longer matters in which sequence your form fields are defined.

To start using the form rendering rules, put a list of form field names into the `form_create_rules`
property one of your admin views::

    class RuleView(sqla.ModelView):
        form_create_rules = ('email', 'first_name', 'last_name')

In this example, only three fields will be rendered and `email` field will be above other two fields.

Whenever Flask-Admin sees a string value in `form_create_rules`, it automatically assumes that it is a
form field reference and creates a :class:`flask_admin.form.rules.Field` class instance for that field.

Lets say we want to display some text between the `email` and `first_name` fields. This can be accomplished by
using the :class:`flask_admin.form.rules.Text` class::

    from flask_admin.form import rules

    class RuleView(sqla.ModelView):
        form_create_rules = ('email', rules.Text('Foobar'), 'first_name', 'last_name')

Built-in rules
*******************

Flask-Admin comes with few built-in rules that can be found in the :mod:`flask_admin.form.rules` module:

======================================================= ========================================================
Form Rendering Rule                                     Description
======================================================= ========================================================
:class:`flask_admin.form.rules.BaseRule`                All rules derive from this class
:class:`flask_admin.form.rules.NestedRule`              Allows rule nesting, useful for HTML containers
:class:`flask_admin.form.rules.Text`                    Simple text rendering rule
:class:`flask_admin.form.rules.HTML`                    Same as `Text` rule, but does not escape the text
:class:`flask_admin.form.rules.Macro`                   Calls macro from current Jinja2 context
:class:`flask_admin.form.rules.Container`               Wraps child rules into container rendered by macro
:class:`flask_admin.form.rules.Field`                   Renders single form field
:class:`flask_admin.form.rules.Header`                  Renders form header
:class:`flask_admin.form.rules.FieldSet`                Renders form header and child rules
======================================================= ========================================================

.. _database-backends:

Using Different Database Backends
----------------------------------------

****

There are five different backends for you to choose
from, depending on which database you would like to use for your application. If, however, you need
to implement your own database backend, have a look at: `adding_a_new_model_backend`_.

SQLAlchemy backend
********************

If you don't know where to start, but you're familiar with relational databases, then you should probably look at using
`SQLAlchemy`_. It is a full-featured toolkit, with support for SQLite, PostgreSQL, MySQL,
Oracle and MS-SQL amongst others. It really comes into its own once you have lots of data, and a fair amount of
relations between your data models. If you want to track spatial data like latitude/longitude
points, you should look into `GeoAlchemy`_, as well.

Notable features:

 - SQLAlchemy 0.6+ support
 - Paging, sorting, filters
 - Proper model relationship handling
 - Inline editing of related models

**Getting Started**

In order to use SQLAlchemy model scaffolding, you need to have:

 1. SQLAlchemy ORM `model <http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html#declare-a-mapping>`_
 2. Initialized database `session <http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html#creating-a-session>`_

If you use Flask-SQLAlchemy, this is how you initialize Flask-Admin
and get session from the `SQLAlchemy` object::

    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    # .. read settings
    db = SQLAlchemy(app)

    # .. model declarations here

    if __name__ == '__main__':
        admin = Admin(app)
        # .. add ModelViews
        # admin.add_view(ModelView(SomeModel, db.session))

**Creating simple model**

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

You can add new models, edit existing, etc.

**Customizing administrative interface**

List view can be customized in different ways.

First of all, you can use various class-level properties to configure
what should be displayed and how. For example, :attr:`~flask_admin.contrib.sqla.ModelView.column_list` can be used to show some of
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

Alternatively, you can override some of the :class:`~flask_admin.contrib.sqla.ModelView` methods and implement your custom logic.

For example, if you need to contribute additional field to the generated form,
you can do something like this::

    class UserView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = TextField('Extra')
            return form_class

Check :doc:`api/mod_contrib_sqla` documentation for list of
configuration properties and methods.

**Multiple Primary Keys**

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

**Example**

Flask-Admin comes with relatively advanced example, which you can
see `here <https://github.com/flask-admin/flask-admin/tree/master/examples/sqla>`_.

MongoEngine backend
*********************

MongoEngine integration example is `here <https://github.com/flask-admin/flask-admin/tree/master/examples/mongoengine>`_.
If you're looking for something simpler, or your data models are reasonably self-contained, then
`MongoEngine`_ could be a better option. It is a python wrapper around the popular
*NoSQL* database called `MongoDB`_.

Features:

 - MongoEngine 0.7+ support
 - Paging, sorting, filters, etc
 - Supports complex document structure (lists, subdocuments and so on)
 - GridFS support for file and image uploads

In order to use MongoEngine integration, you need to install the `flask-mongoengine` package,
as Flask-Admin uses form scaffolding from it.

You don't have to use Flask-MongoEngine in your project - Flask-Admin will work with "raw"
MongoEngine models without any problems.

Known issues:

 - Search functionality can't split query into multiple terms due to
   MongoEngine query language limitations

For more documentation, check :doc:`api/mod_contrib_mongoengine` documentation.

Peewee backend
*****************

Features:

 - Peewee 2.x+ support;
 - Paging, sorting, filters, etc;
 - Inline editing of related models;

In order to use peewee integration, you need to install two additional Python packages: `peewee` and `wtf-peewee`.

Known issues:

 - Many-to-Many model relations are not supported: there's no built-in way to express M2M relation in Peewee

For more documentation, check :doc:`api/mod_contrib_peewee` documentation.

Peewee example is `here <https://github.com/flask-admin/flask-admin/tree/master/examples/peewee>`_.

PyMongo backend
*****************

Pretty simple PyMongo backend.

Flask-Admin does not make assumptions about document structure, so you
will have to configure ModelView to do what you need it to do.

This is bare minimum you have to provide for Flask-Admin view to work
with PyMongo:

 1. Provide list of columns by setting `column_list` property
 2. Provide form to use by setting `form` property
 3. When instantiating :class:`flask_admin.contrib.pymongo.ModelView` class, you have to provide PyMongo collection object

This is minimal PyMongo view::

  class UserForm(Form):
      name = TextField('Name')
      email = TextField('Email')

  class UserView(ModelView):
      column_list = ('name', 'email')
      form = UserForm

  if __name__ == '__main__':
      admin = Admin(app)

      # 'db' is PyMongo database object
      admin.add_view(UserView(db['users']))

On top of that you can add sortable columns, filters, text search, etc.

For more documentation, check :doc:`api/mod_contrib_pymongo` documentation.

PyMongo integration example is `here <https://github.com/flask-admin/flask-admin/tree/master/examples/pymongo>`_.


Migrating from Django
-------------------------

****

If you are used to `Django <https://www.djangoproject.com/>`_ and the *django-admin* package, you will find
Flask-Admin to work slightly different from what you would expect.

Design Philosophy
****************************

In general, Django and *django-admin* strives to make life easier by implementing sensible defaults. So a developer
will be able to get an application up in no time, but it will have to conform to most of the defaults. Of course it
is possible to customize things, but this often requires a good understanding of what's going on behind the scenes,
and it can be rather tricky and time-consuming.

The design philosophy behind Flask is slightly different. It embraces the diversity that one tends to find in web
applications by not forcing design decisions onto the developer. Rather than making it very easy to build an
application that *almost* solves your whole problem, and then letting you figure out the last bit, Flask aims to make it
possible for you to build the *whole* application. It might take a little more effort to get started, but once you've
got the hang of it, the sky is the limit... Even when your application is a little different from most other
applications out there on the web.

Flask-Admin follows this same design philosophy. So even though it provides you with several tools for getting up &
running quickly, it will be up to you, as a developer, to tell Flask-Admin what should be displayed and how. Even
though it is easy to get started with a simple `CRUD <http://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_
interface for each model in your application, Flask-Admin doesn't fix you to this approach, and you are free to
define other ways of interacting with some, or all, of your models.

Due to Flask-Admin supporting more than one ORM (SQLAlchemy, MongoEngine, Peewee, raw pymongo), the developer is even
free to mix different model types into one application by instantiating appropriate CRUD classes.

Here is a list of some of the configuration properties that are made available by Flask-Admin and the
SQLAlchemy backend. You can also see which *django-admin* properties they correspond to:

=========================================== ==============================================
Django                                      Flask-Admin
=========================================== ==============================================
actions										:attr:`~flask_admin.actions`
exclude										:attr:`~flask_admin.model.BaseModelView.form_excluded_columns`
fields										:attr:`~flask_admin.model.BaseModelView.form_columns`
form 										:attr:`~flask_admin.model.BaseModelView.form`
formfield_overrides 						:attr:`~flask_admin.model.BaseModelView.form_args`
inlines										:attr:`~flask_admin.contrib.sqlalchemy.ModelView.inline_models`
list_display 								:attr:`~flask_admin.model.BaseModelView.column_list`
list_filter									:attr:`~flask_admin.contrib.sqlalchemy.ModelView.column_filters`
list_per_page 								:attr:`~flask_admin.model.BaseModelView.page_size`
search_fields								:attr:`~flask_admin.model.BaseModelView.column_searchable_list`
add_form_template							:attr:`~flask_admin.model.BaseModelView.create_template`
change_form_template						:attr:`~flask_admin.model.BaseModelView.change_form_template`
=========================================== ==============================================

You might want to check :doc:`api/mod_model` for basic model configuration options (reused by all model
backends) and specific backend documentation, for example :doc:`api/mod_contrib_sqla`. There's much more
than what is displayed in this table.

Adding a Redis console
--------------------------

****


Overriding the Form Scaffolding
---------------------------------

****

If you don't want to the use the built-in Flask-Admin form scaffolding logic, you are free to roll your own
by simply overriding :meth:`~flask_admin.model.base.scaffold_form`. For example, if you use
`WTForms-Alchemy <https://github.com/kvesteri/wtforms-alchemy>`_, you could put your form generation code
into a `scaffold_form` method in your `ModelView` class.

For SQLAlchemy, if the `synonym_property` does not return a SQLAlchemy field, then Flask-Admin won't be able to figure out what to
do with it, so it won't generate a form field. In this case, you would need to manually contribute your own field::

    class MyView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = TextField('Extra')
            return form_class

Usage Tips
---------------

****

Initialisation: As an alternative to passing a Flask application object to the Admin constructor, you can also call the
:meth:`~flask_admin.base.Admin.init_app` function, after the Admin instance has been initialized::

        admin = Admin(name='microblog', template_mode='bootstrap3')
        # Add views here
        admin.init_app(app)