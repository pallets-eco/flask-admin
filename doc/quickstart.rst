Quick Start
===========

This page gives quick introduction to Flask-AdminEx library. It is assumed that reader has some prior
knowledge of Flask framework.

Introduction
------------

While developing the library, I had set of goals which should make it very easy to use and won't
require monkey patching to achieve desired functionality. Here they are:

1. It should be flexible
2. It should be reusable
3. It should look nice

Library uses one simple, but powerful concept - administrative pieces are grouped by functionality
into classes with their own view methods.

Here is absolutely valid administrative piece::

    class MyAdminView(BaseView):
        @expose('/')
        def index(self):
            return render_template('admin/myindex.html', view=self)

        @expose('/test/')
        def test(self):
            return render_template('admin/test.html', view=self)


With this approach, all of OOP concepts apply. You can derive, you can modify behavior, you can do
whatever you want.

Initialization
--------------

You must create `Admin` class and associate it with the `Flask` application::

    from flask import Flask
    from flask.ext.adminex import Admin

    app = Flask(__name__)

    admin = Admin()
    admin.setup_app(app)

    app.run()

If you will run this application and will navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see lonely Home page with a navigation bar on top.

You can change application name by passing `name` parameter to the `Admin` class constructor::

    admin = Admin(name='My App')
    admin.setup_app(app)


Adding first view
-----------------

Now, lets add custom view::

    from flask import Flask
    from flask.ext.adminex import Admin, BaseView

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

    app = Flask(__name__)

    admin = Admin()
    admin.add_view(MyView(name='Hello'))
    admin.setup_app(app)

    app.run()

If you will run this example, you will see that menu has two items: Home and Hello. If you click on the Hello menu
item, application will crash, as you did not create 'index.html' template.

Create templates directory and create new index.html file with following contents::

    {% extends 'admin/master.html' %}
    {% block body %}
        Hello World from MyView!
    {% endblock %}

All administrative pages should derive from the 'admin/master.html' to maintain same look and feel.

If you will refresh 'Hello' administrative page again you should see greeting in the content section.

Authentication
--------------

By default, administrative interface will be visible to everyone, as Flask-AdminEx does not make
any assumptions about authentication system you're using.

If you want to control who can access administrative views and who can not, derive from the
administrative view class and implement `is_accessible` method::

    class MyView(BaseView):
        def is_accessible(self):
            return login.current_user.is_authenticated()


Menu is generated dynamically, so you can implement policy based security, so some users will see
some of the administrative interface, others won't be able to, etc.

Generating URLs
---------------

Internally, these view classes work on top of Flask blueprints, so you can use `url_for` with a dot
prefix to get URL to a local view::

    class MyView(BaseView):
        @expose('/')
        def index(self)
            # Get URL for the `test` view method
            url = url_for('.test')
            return self.render('index.html', url=url)

        @expose('/test/')
        def test(self):
            return self.render('test.html')

If you want to generate URL to the particular view method from outside, following rules apply:

1. You have ability to override endpoint name by passing `endpoint` parameter to the view class
constructor::

    admin = Admin()
    admin.add_view(MyView(endpoint='testadmin'))
    admin.setup_app(app)

In this case, you can generate links by concatenating view method name with a endpoint::

    url_for('testadmin.index')

2. If you don't override endpoint name, it will use lower case class name. For previous example,
code to get URL will look like::

    url_for('myview.index')

3. For model-based views rule is different - it will take model class name, if endpoint name
is not provided. Model-based views will be explained in the next section.


Model Views
-----------

Flask-AdminEx comes with built-in SQLAlchemy model administrative interface. It is very easy to use it::

    from flask.ext.adminex.ext.sqlamodel import ModelBase
    from flask.ext.sqlalchemy import db

    # Flask and Flask-SQLAlchemy initialization here

    admin = Admin()
    admin.add_view(ModelBase(User, db.session, name='Users'))
    admin.setup_app(app)

This will create administrative interface for `User` model with default settings.

If you want to customize model views, you have two options:

1. Change behavior by overriding public properties that control how these views work
2. Change behavior by overriding view methods

For example, if you want to disable model creation, show only 'login' and 'email' columns in the list view,
you can do something like this::

    class UserView(ModelBase):
        # Disable model creation
        can_create = False

        # Override displayed fields
        list_columns = ('login', 'email')

        def __init__(self, session):
            __super__(MyView, self).__init__(User, session)

    admin = Admin()
    admin.add_view(UserView(db.session))
    admin.setup_app(app)

It is very easy to add support for different database backends (Mongo, etc) by inheriting from `BaseModelView`
class and implementing database-related methods.

Please refer to documentation on how to customize behavior of model-based administrative views.

Examples
--------

Flask-AdminEx comes with three samples:

- Simple administrative interface with custom administrative views
- Sample model view interface
- Flask-Login integration sample
