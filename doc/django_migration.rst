Migrating from Django
=====================

If you used `Django <https://www.djangoproject.com/>`_ before, you might find Flask-Admin work slightly different than you expect.

This guide will help you to get acquainted with the Flask-Admin library. Some prior Flask knowledge will be required.

Architecture
------------

Django does lots of things automatically. For example, it is importing models from the `models.py`, administrative interface
declarations from `admin.py` and so on.

Flask philosophy is slightly different - explicit is better than implicit. If something should be initialized, it should be
initialized by the developer.

Flask-Admin follows this convention. It is up for you, as a developer, to tell Flask-Admin what should be displayed and how.

Sometimes this will require writing a bit of boilerplate code, but it will pay off in the future, especially if you
will have to implement some custom logic.

All Flask-Admin functionality is incapsulated into classes with view methods. Class should be instantiated and plugged to the
administrative framework for its views to be accessible by the users. Nothing prevents from creating more than one instance
of the class and plug them using different base URL - it will work as expected.

Another big difference - Flask-Admin is not built around model CRUD interface. CRUD is just extension of the base administrative
framework. In a nutshell, it is just a class which accepts model in its constructor and exposes few views (list, create, edit, etc).
And as Flask-Admin supports more than one ORM (SQLAlchemy, MongoEngine, Peewee, raw pymongo), developer can mix different model
types in one application by instantiating appropriate CRUD classes.

Getting started
---------------

Lets write a bit of code to create CRUD interface for `Post` SQLAlchemy model. This example uses Flask-SQLAlchemy extension,
but you don't have to use it, Flask-Admin will work with SQLAlchemy declarative extension too. To the code::

    from flask import Flask
    from flask.ext.admin import Admin
    from flask.ext.admin.contrib.sqla import ModelView
    from flask.ext.sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    db = SQLAlchemy(app)

    class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.Unicode(120))
        text = db.Column(db.UnicodeText, nullable=False)

    admin = Admin(app)
    admin.add_view(ModelView(Post, db.session))

You can customize behavior of CRUD interface by using special properties, like Django does::

    # ... imports

    class PostView(ModelView):
        list_columns = ('title',)

        def __init__(self):
            super(PostView, self).__init__(Post, db.session)

    # ... initialization

    admin.add_view(PostView())

But because administrative interface is implemented as class, you can customize it in constructor as well::

    class PostView(ModelView):
        list_columns = ('title',)

        def __init__(self, include_id=False):
            if include_id:
                self.list_columns = ('id', 'title')

            super(PostView, self).__init__(Post, db.session)

Here is comparison table between some Django configuration properties and Flask-Admin SQLAlchemy backend properties:

=========================================== ==============================================
Django                                      Flask-Admin
=========================================== ==============================================
actions										:doc:`api/mod_actions`
exclude										:attr:`~flask.ext.admin.model.BaseModelView.form_excluded_columns`
fields										:attr:`~flask.ext.admin.model.BaseModelView.form_columns`
form 										:attr:`~flask.ext.admin.model.BaseModelView.form`
formfield_overrides 						:attr:`~flask.ext.admin.model.BaseModelView.form_args`
inlines										:attr:`~flask.ext.admin.contrib.sqlalchemy.ModelView.inline_models`
list_display 								:attr:`~flask.ext.admin.model.BaseModelView.column_list`
list_filter									:attr:`~flask.ext.admin.contrib.sqlalchemy.ModelView.column_filters`
list_per_page 								:attr:`~flask.ext.admin.model.BaseModelView.page_size`
search_fields								:attr:`~flask.ext.admin.model.BaseModelView.column_searchable_list`
add_form_template							:attr:`~flask.ext.admin.model.BaseModelView.create_template`
change_form_template						:attr:`~flask.ext.admin.model.BaseModelView.change_form_template`
=========================================== ==============================================

You might want to check :doc:`api/mod_model` for basic model configuration options (reused by all model
backends) and specific backend documentation, for example :doc:`api/mod_contrib_sqla`. There's much more
than displayed in this table.

Authentication
--------------

If you need to restrict access to the administrative interface, you need to override `is_accessible` method. For example::

    class MyModelView(ModelView):
        def is_accessible(self):
            return login.current_user.is_authenticated()

If administrative piece is not accessible by the user, it won't be displayed in the menu as well.

Templates
---------

Flask-Admin uses Jinja2 templating engine. Jinja2 is pretty advanced templating engine and Flask-Admin templates were made
to be easily extensible.

For example, if you need to include javascript snippet on edit page for your model, it is easy to do::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
        {{ super() }}
        <script language="javascript">alert('Hello World!')</script>
    {% endblock %}

And then point your class to this new template::

    class MyModelView(ModelView):
        edit_template = 'my_edit_template.html'

For list of template blocks, check :doc:`templates`.

Tips and hints
--------------

 1. Programming with Flask-Admin is not very different from normal application development - write some views, expose
    them to the user in constistent user interface.

 2. If you're missing some functionality which can be used more than once, you can create your own "base" class and use
    it instead of default implementation

 3. Due to more advanced templating engine, you can easily extend existing templates. You can even change look and feel
    of the administrative UI completely, if you want to. Check `this example <https://github.com/mrjoes/flask-admin/tree/master/examples/layout>`_.

 4. You're not limited to CRUD interface. Want to add some kind of realtime monitoring via websockets? No problem at all

 5. There's so called "index view". By default it is empty, but you can put any information you need there. It is displayed
    under Home menu option.

