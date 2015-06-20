Flask-Admin
===========

Flask-Admin is a batteries-included, simple-to-use `Flask <http://flask.pocoo.org/>`_ extension that lets you
add admin interfaces to Flask applications. It is inspired by the *django-admin* package, but implemented in such
a way that the developer has total control of the look, feel and functionality of the resulting application.

Browse through the documentation below to learn more about what you can do with Flask-Admin. Or head over to
`our GitHub repository <http://github.com/flask-admin/flask-admin>`_ to find out how you can contribute to the project.


This page gives a quick introduction to the Flask-Admin library. It is assumed that the reader has some prior
knowledge of the `Flask <http://flask.pocoo.org/>`_ framework.

If you're a Django user, you might also find the :doc:`django_migration` guide helpful.

Introduction
------------

The library is intended to be as flexible as possible. And the developer should
not need to monkey-patch anything to achieve desired functionality.

The library uses one simple, but powerful concept - administrative pieces are built as classes with
view methods.

For example, here is an absolutely valid administrative piece::

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('admin/myindex.html')

        @expose('/test/')
        def test(self):
            return self.render('admin/test.html')

If the user visits the *index* view, the *admin/myindex.html* template will be rendered. In the same way, visiting
the *test* view will result in the *admin/test.html* view being rendered.

So, how does this approach help in structuring an admin interface? With such building blocks, you're
implementing reusable functional pieces that are highly customizable.

For example, Flask-Admin provides a ready-to-use SQLAlchemy model interface. It is implemented as a
class which accepts two parameters: the model class and a database session. While it exposes some
class-level variables which change behavior of the interface (somewhat similar to django.contrib.admin),
nothing prohibits you from inheriting from it and overriding the form creation logic, database access methods
or extend existing functionality by adding more views.



.. toctree::
   :maxdepth: 2

   getting_started
   authorisation_and_permissions
   customising_builtin_views
   adding_your_own_views
   advanced
   api/index


Examples
--------

Flask-Admin comes with several examples, that will really help you get a grip on what's possible.
Browse through them in the GitHub repo, and then run them locally to get yourself up to speed in no time:

- `Simple views <https://github.com/flask-admin/Flask-Admin/tree/master/examples/simple>`_
    Here we show how to add some simple custom views to your admin interface. They don't have to
    be associated to any of your database models. You can fill them with whatever content you want.

- `Custom layout <https://github.com/flask-admin/Flask-Admin/tree/master/examples/layout>`_
    Override some of the built-in templates to get complete control over the look and feel of your Admin interface. Either
    while using the default Bootstrap 2, or the newer `Bootstrap 3 <https://github.com/flask-admin/Flask-Admin/tree/master/examples/layout_bootstrap3>`_.

- `SQLAlchemy model example <https://github.com/flask-admin/Flask-Admin/tree/master/examples/sqla>`_
    Model-based views provide heaps of builtin goodness, making it really easy to get a set of the default CRUD views in place.
    This example shows some of the basics.

- `SQLAlchemy model views with custom forms and file handling <https://github.com/flask-admin/Flask-Admin/tree/master/examples/forms>`_
    Here, we show some of the more interesting things you can do with very little effort, including customizing the
    builtin forms, and adding support for handling file/image uploads.

- `Flask-Login integration example <https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth>`_
    Use Flask-Login for authentication to hide some of your admin views behind a login wall.

- `Peewee model example <https://github.com/flask-admin/Flask-Admin/tree/master/examples/peewee>`_
    Not so keen on SQLAlchemy? Perhaps you'd rather use Peewee?

- `MongoEngine model example <https://github.com/flask-admin/Flask-Admin/tree/master/examples/mongoengine>`_
   ... or check this example if MongoDB is more your style.

- `I18n and L10n with Flask-BabelEx <https://github.com/flask-admin/Flask-Admin/tree/master/examples/babel>`_
   Do you need to make your Admin interface available in other languages? Luckily, Flask-Admin is built for just that kind of thing.

- `Redis terminal <https://github.com/flask-admin/Flask-Admin/tree/master/examples/rediscli>`_
   If you use Redis for caching, then check this example to see how easy it is to add a Redis terminal to your Admin
   interface, so you can reach your Redis instance straight from a browser.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
