Quick Start
===========

This page gives quick introduction to Flask-AdminEx library. It is assumed that reader has some prior
knowledge of the `Flask <http://flask.pocoo.org/>`_ framework.

Introduction
------------

While developing the library, I attempted to make it as flexible as possible. Developer should
not monkey-patch anything to achieve desired functionality.

Library uses one simple, but powerful concept - administrative pieces are built as classes with
view methods.

Here is absolutely valid administrative piece::

    class MyAdminView(BaseView):
        @expose('/')
        def index(self):
            return self.render('admin/myindex.html')

        @expose('/test/')
        def test(self):
            return self.render('admin/test.html')

So, how does it help structuring administrative interface? With such building blocks, you're
implementing reusable functional pieces that are highly customizable.

For example, Flask-AdminEx provides ready-to-use SQLAlchemy model interface. It is implemented as a
class which accepts two parameters: model and a database session. While it exposes some
class-level variables which change behavior of the interface (somewhat similar to django.contrib.admin),
nothing prohibits you from overriding form creation logic, database access methods or adding more views.

Initialization
--------------

To start using Flask-AdminEx, you have to create `Admin` class instance and associate it with Flask application::

    from flask import Flask
    from flask.ext.adminex import Admin

    app = Flask(__name__)

    admin = Admin(app)
    # Add administrative views here

    app.run()

If you start this application and navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see empty "Home" page with a navigation bar on top

    .. image:: images/quickstart/quickstart_1.png
        :target: ../_images/quickstart_1.png

You can change application name by passing `name` parameter to the `Admin` class constructor::

    admin = Admin(app, name='My App')

Name is displayed in the menu section.

You don't have to pass Flask application object to the constructor - you can call `init_app` later::

    admin = Admin(name='My App')
    # Add views here
    admin.init_app(app)

Adding view
-----------

Now, lets add a view. To do this, you need to derive from `BaseView` class::

    from flask import Flask
    from flask.ext.adminex import Admin, BaseView, expose

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

    app = Flask(__name__)

    admin = Admin(app)
    admin.add_view(MyView(name='Hello'))

    app.run()

If you will run this example, you will see that menu has two items: Home and Hello.

Each view class should have default page - view method with '/' url. Following code won't work::

    class MyView(BaseView):
        @expose('/index/')
        def index(self):
            return self.render('index.html')

Now, create `templates` directory and then create new `index.html` file with following content::

    {% extends 'admin/master.html' %}
    {% block body %}
        Hello World from MyView!
    {% endblock %}

All administrative pages should derive from the 'admin/master.html' to maintain same look and feel.

If you will refresh 'Hello' administrative page again you should see greeting in the content section.

    .. image:: images/quickstart/quickstart_2.png
        :width: 640
        :target: ../_images/quickstart_2.png

You're not limited to top level menu. It is possible to pass category name and it will be used as a
top menu item. For example::

    from flask import Flask
    from flask.ext.adminex import Admin, BaseView, expose

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

    app = Flask(__name__)

    admin = Admin(app)
    admin.add_view(MyView(name='Hello 1', endpoint='test1', category='Test'))
    admin.add_view(MyView(name='Hello 2', endpoint='test2', category='Test'))
    admin.add_view(MyView(name='Hello 3', endpoint='test3', category='Test'))
    app.run()

Will look like this:

    .. image:: images/quickstart/quickstart_3.png
        :width: 640
        :target: ../_images/quickstart_3.png

Authentication
--------------

By default, administrative interface is visible to everyone, as Flask-AdminEx does not make
any assumptions about authentication system you're using.

If you want to control who can access administrative views and who can not, derive from the
administrative view class and implement `is_accessible` method. So, if you use Flask-Login and
want to expose administrative interface only to logged in users, you can do something like
this::

    class MyView(BaseView):
        def is_accessible(self):
            return login.current_user.is_authenticated()


Menu is generated dynamically, so you can implement policy-based security and conditionally
allow or disallow access to parts of the administrative interface.

Generating URLs
---------------

Internally, view classes work on top of Flask blueprints, so you can use `url_for` with a dot
prefix to get URL to a local view::

    class MyView(BaseView):
        @expose('/')
        def index(self)
            # Get URL for the test view method
            url = url_for('.test')
            return self.render('index.html', url=url)

        @expose('/test/')
        def test(self):
            return self.render('test.html')

If you want to generate URL to the particular view method from outside, following rules apply:

1. You have ability to override endpoint name by passing `endpoint` parameter to the view class
constructor::

    admin = Admin(app)
    admin.add_view(MyView(endpoint='testadmin'))

In this case, you can generate links by concatenating view method name with a endpoint::

    url_for('testadmin.index')

2. If you don't override endpoint name, it will use lower case class name. For previous example,
code to get URL will look like::

    url_for('myview.index')

3. For model-based views rule is different - it will take model class name, if endpoint name
is not provided. Model-based views will be explained in the next section.


Model Views
-----------

Flask-AdminEx comes with built-in SQLAlchemy model administrative interface. It is very easy to use::

    from flask.ext.adminex.ext.sqlamodel import ModelView
    from flask.ext.sqlalchemy import db

    # Flask and Flask-SQLAlchemy initialization here

    admin = Admin(app)
    admin.add_view(ModelBase(User, db.session))

This will create administrative interface for `User` model with default settings.

Here is how default list view looks like:

    .. image:: images/quickstart/quickstart_4.png
        :width: 640
        :target: ../_images/quickstart_4.png

If you want to customize model views, you have two options:

1. Change behavior by overriding public properties that control how view works
2. Change behavior by overriding methods

For example, if you want to disable model creation, show only 'login' and 'email' columns in the list view,
you can do something like this::

    class UserView(ModelBase):
        # Disable model creation
        can_create = False

        # Override displayed fields
        list_columns = ('login', 'email')

        def __init__(self, session):
            __super__(MyView, self).__init__(User, session)

    admin = Admin(app)
    admin.add_view(UserView(db.session))

It is very easy to add support for different database backends (Mongo, etc) by inheriting from `BaseModelView`
class and implementing database-related methods.

Please refer to :mod:`flask.ext.adminex.ext.sqlamodel` documentation on how to customize behavior of model-based administrative views.

File Admin
----------

Flask-AdminEx comes with another handy battery - file admin. It gives you ability to manage files on your server (upload, delete, rename, etc).

Here is simple example::

    from flask.ext.adminex.ext.fileadmin import FileAdmin

    import os.path as op

    # Flask setup here

    admin = Admin(app)

    path = op.join(op.dirname(__file__), 'static')
    admin.add_view(path, '/static/', name='Static Files')

Sample screenshot:

    .. image:: images/quickstart/quickstart_5.png
        :width: 640
        :target: ../_images/quickstart_5.png

You can disable uploads, disable file or directory deletion, restrict file uploads to certain types and so on.
Check :mod:`flask.ext.adminex.ext.fileadmin` documentation on how to do it.

Examples
--------

Flask-AdminEx comes with four samples:

- `Simple administrative interface <https://github.com/MrJoes/Flask-AdminEx/tree/master/examples/simple>`_ with custom administrative views
- `SQLAlchemy model example <https://github.com/MrJoes/Flask-AdminEx/tree/master/examples/sqla>`_
- `Flask-Login integration example <https://github.com/MrJoes/Flask-AdminEx/tree/master/examples/auth>`_
- `File management interface <https://github.com/MrJoes/Flask-AdminEx/tree/master/examples/file>`_
