Migrating from Django
=====================

If you are used to `Django <https://www.djangoproject.com/>`_ and the *django-admin* package, you will find
Flask-Admin to work slightly different from what you would expect.

This guide will help you to get acquainted with the Flask-Admin library. It is assumed that you have some prior
knowledge of `Flask <http://flask.pocoo.org/>`_ .

Design Philosophy
-----------------

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
---------------

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

Authentication
--------------

To restrict access to your admin interface, you can implement your own class for creating admin components, and
override the `is_accessible` method::

    class MyModelView(ModelView):
        def is_accessible(self):
            return login.current_user.is_authenticated()

Components that are not accessible to a particular user, will also not be displayed in the menu for that user.

Templates
---------

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

Tips and hints
--------------

 1. Programming with Flask-Admin is not very different from normal application development - write some views and expose
    them to the user, using templates to create a consistent user experience.

 2. If you are missing some functionality which can be used more than once, you can create your own "base" class and use
    it instead of default implementation.

 3. Using Jinja2, you can easily extend the existing templates. You can even change the look and feel of the admin
    interface completely, if you want to. Check `this example <https://github.com/mrjoes/flask-admin/tree/master/examples/layout>`_.

 4. You are not limited to a simple CRUD interface for every model. Want to add some kind of realtime monitoring via websockets? No problem.

 5. There's a so called "index view". By default it is empty, but you can put any information you need there. It is displayed
    under the *Home* menu option.
