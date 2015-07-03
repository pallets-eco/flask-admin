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

Initialisation
---------------

****

As an alternative to passing a Flask application object to the Admin constructor, you can also call the
:meth:`~flask_admin.base.Admin.init_app` function, after the Admin instance has been initialized::

        admin = Admin(name='My App', template_mode='bootstrap3')
        # Add views here
        admin.init_app(app)

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

   So, you could try out a French version of the application at: `http://localhost:5000/admin/?lang=fr <http://localhost:5000/admin/?lang=fr>`_.

#. Add your own logic to the locale selector function:

   The application could store locale in
   a user profile, cookie, session, etc. And it could interrogate the `Accept-Language`
   header for making the selection automatically.

If the builtin translations are not enough, look at the `Flask-BabelEx documentation <https://pythonhosted.org/Flask-BabelEx/>`_
to see how you can add your own.

Handling Foreign Key relations inline
--------------------------------------------

****


Many-to-many relations
----------------------------------

****

.. _file-admin:

Managing Files & Folders
--------------------------------

****

Flask-Admin comes with another handy battery - file admin. It gives you the ability to manage files on your server
(upload, delete, rename, etc).

Here is simple example::

    from flask_admin.contrib.fileadmin import FileAdmin

    import os.path as op

    # Flask setup here

    admin = Admin(app)

    path = op.join(op.dirname(__file__), 'static')
    admin.add_view(FileAdmin(path, '/static/', name='Static Files'))

Sample screenshot:

    .. image:: images/quickstart/quickstart_5.png
        :width: 640
        :target: ../_images/quickstart_5.png

You can disable uploads, disable file or directory deletion, restrict file uploads to certain types and so on.
Check :mod:`flask_admin.contrib.fileadmin` documentation on how to do it.

Managing geographical models
--------------------------------------

****

GeoAlchemy backend

If you want to store spatial information in a GIS database, Flask-Admin has
you covered. The `GeoAlchemy`_ backend extends the SQLAlchemy backend (just as
GeoAlchemy extends SQLAlchemy) to give you a pretty and functional map-based
editor for your admin pages.

Notable features:

 - Uses the amazing `Leaflet`_ Javascript library for displaying maps,
   with map data from `Mapbox`_
 - Uses `Leaflet.Draw`_ for editing geographic information interactively,
   including points, lines, and polygons
 - Graceful fallback to editing `GeoJSON`_ data in a ``<textarea>``, if the
   user has turned off Javascript
 - Works with a `Geometry`_ SQL field that is integrated with `Shapely`_ objects

Getting Started
^^^^^^^^^^^^^^^^^^

GeoAlchemy is based on SQLAlchemy, so you'll need to complete the "getting started"
directions for SQLAlchemy backend first. For GeoAlchemy, you'll also need a
map ID from `Mapbox`_, a map tile provider. (Don't worry, their basic plan
is free, and works quite well.) Then, just include the map ID in your application
settings::

    app = Flask(__name__)
    app.config['MAPBOX_MAP_ID'] = "example.abc123"

To use the v4 of their API (the default is v3):::

    app.config['MAPBOX_ACCESS_TOKEN'] = "pk.def456"

.. note::
  Leaflet supports loading map tiles from any arbitrary map tile provider, but
  at the moment, Flask-Admin only supports Mapbox. If you want to use other
  providers, make a pull request!

Creating simple model
^^^^^^^^^^^^^^^^^^^^^^^^

GeoAlchemy comes with a `Geometry`_ field that is carefully divorced from the
`Shapely`_ library. Flask-Admin will use this field so that there are no
changes necessary to other code. ``ModelView`` should be imported from
``geoa`` rather than the one imported from ``sqla``::

    from geoalchemy2 import Geometry
    from flask_admin.contrib.geoa import ModelView

    # .. flask initialization
    db = SQLAlchemy(app)

    class Location(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), unique=True)
        point = db.Column(Geometry("POINT"))

    if __name__ == '__main__':
        admin = Admin(app)
        admin.add_view(ModelView(User, db.session))

        db.create_all()
        app.run('0.0.0.0', 8000)

Limitations
^^^^^^^^^^^^^^

There's currently no way to sort, filter, or search on geometric fields
in the admin. It's not clear that there's a good way to do so.
If you have any ideas or suggestions, make a pull request!

.. _GeoAlchemy: http://geoalchemy-2.readthedocs.org/
.. _Leaflet: http://leafletjs.com/
.. _Leaflet.Draw: https://github.com/Leaflet/Leaflet.draw
.. _Shapely: http://toblerity.org/shapely/
.. _Mapbox: https://www.mapbox.com/
.. _GeoJSON: http://geojson.org/
.. _Geometry: http://geoalchemy-2.readthedocs.org/en/latest/types.html#geoalchemy2.types.Geometry

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

Getting started
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^

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

Enabling CSRF Validation
-----------------------------

****

Adding CSRF validation will require overriding the :class:`flask_admin.form.BaseForm` by using :attr:`flask_admin.model.BaseModelView.form_base_class`.

WTForms >=2::

    from wtforms.csrf.session import SessionCSRF
    from wtforms.meta import DefaultMeta
    from flask import session
    from datetime import timedelta
    from flask_admin import form
    from flask_admin.contrib import sqla

    class SecureForm(form.BaseForm):
        class Meta(DefaultMeta):
            csrf = True
            csrf_class = SessionCSRF
            csrf_secret = b'EPj00jpfj8Gx1SjnyLxwBBSQfnQ9DJYe0Ym'
            csrf_time_limit = timedelta(minutes=20)

            @property
            def csrf_context(self):
                return session

    class ModelAdmin(sqla.ModelView):
        form_base_class = SecureForm

For WTForms 1, you can use use Flask-WTF's Form class::

    import os
    import flask
    import flask_wtf
    import flask_admin
    import flask_sqlalchemy
    from flask_admin.contrib.sqla import ModelView

    DBFILE = 'app.db'

    app = flask.Flask(__name__)
    app.config['SECRET_KEY'] = 'Dnit7qz7mfcP0YuelDrF8vLFvk0snhwP'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DBFILE
    app.config['CSRF_ENABLED'] = True

    flask_wtf.CsrfProtect(app)
    db = flask_sqlalchemy.SQLAlchemy(app)
    admin = flask_admin.Admin(app, name='Admin')

    class MyModelView(ModelView):
        # Here is the fix:
        form_base_class = flask_wtf.Form

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String)
        password = db.Column(db.String)

    if not os.path.exists(DBFILE):
        db.create_all()

    admin.add_view( MyModelView(User, db.session, name='User') )

    app.run(debug=True)


.. _database-backends:

Using Different Database Backends
----------------------------------------

****

The purpose of Flask-Admin is to help you manage your data. For this, it needs some database backend in order to be
able to access that data in the first place. At present, there are five different backends for you to choose
from, depending on which database you would like to use for your application.

.. toctree::
   :maxdepth: 2

   db_sqla
   db_mongoengine
   db_peewee
   db_pymongo
   adding_a_new_model_backend

If you don't know where to start, but you're familiar with relational databases, then you should probably look at using
`SQLAlchemy`_. It is a full-featured toolkit, with support for SQLite, PostgreSQL, MySQL,
Oracle and MS-SQL amongst others. It really comes into its own once you have lots of data, and a fair amount of
relations between your data models. If you want to track spatial data like latitude/longitude
points, you should look into `GeoAlchemy`_, as well.

If you're looking for something simpler, or your data models are reasonably self-contained, then
`MongoEngine`_ could be a better option. It is a python wrapper around the popular
*NoSQL* database called `MongoDB`_.

Of course, if you feel that there's an awesome database wrapper that is missing from the list above, we'd greatly
appreciate it if you could write the plugin for it and submit it as a pull request. A special section of these docs
are dedicated to helping you through this process. See :doc:`model_guidelines`.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _GeoAlchemy: http://geoalchemy-2.readthedocs.org/
.. _MongoEngine: http://mongoengine.org/
.. _MongoDB: http://www.mongodb.org/

Migrating from Django
-------------------------

****

If you are used to `Django <https://www.djangoproject.com/>`_ and the *django-admin* package, you will find
Flask-Admin to work slightly different from what you would expect.

This guide will help you to get acquainted with the Flask-Admin library. It is assumed that you have some prior
knowledge of `Flask <http://flask.pocoo.org/>`_ .

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

Getting started
****************************

At the basis of Flask-Admin is the idea that you can add components to your admin interface by declaring a separate
class for each component, and then adding a method to that class for every view that should be associated to the
component. Since classes can inherit from one another, and since several instances of the same class can be created,
this approach allows for a great deal of flexibility.

Let's write a bit of code to create a simple CRUD interface for the `Post` SQLAlchemy model. The example below uses the
Flask-SQLAlchemy extension, but you don't have to use it (you could also use the SQLAlchemy declarative extension)::

    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    db = SQLAlchemy(app)

    class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.Unicode(120))
        text = db.Column(db.UnicodeText, nullable=False)

    admin = Admin(app)
    admin.add_view(ModelView(Post, db.session))

To customize the behavior of the model's CRUD interface, you can set values for some of the special
properties (as listed below) that are made available through `model.BaseModelView`, or one of the ORM wrappers::

    # ... imports

    class PostView(ModelView):
        list_columns = ('title',)

        def __init__(self):
            super(PostView, self).__init__(Post, db.session)

    # ... initialization

    admin.add_view(PostView())

Because each component is implemented as a class, you can also customize it in the constructor::

    class PostView(ModelView):
        list_columns = ('title',)

        def __init__(self, include_id=False):
            if include_id:
                self.list_columns = ('id', 'title')

            super(PostView, self).__init__(Post, db.session)

Here is a list of some of the configuration properties that are made available by Flask-Admin and the
SQLAlchemy backend. You can also see which *django-admin* properties they correspond to:

=========================================== ==============================================
Django                                      Flask-Admin
=========================================== ==============================================
actions										:doc:`api/mod_actions`
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

Templates
***********

Flask-Admin uses Jinja2 templating engine. Jinja2 is pretty advanced templating engine and Flask-Admin templates were made
to be easily extensible.

For example, if you need to include a javascript snippet on the *Edit* page for one of your models, you could::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
        {{ super() }}
        <script language="javascript">alert('Hello World!')</script>
    {% endblock %}

and then point your class to this new template::

    class MyModelView(ModelView):
        edit_template = 'my_edit_template.html'

For list of available template blocks, check :doc:`templates`.

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

