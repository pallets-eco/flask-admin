Flask-Admin
===========

The project was recently moved into its own organization. Please update your
references to *git@github.com:flask-admin/flask-admin.git*.

.. image:: https://d322cqt584bo4o.cloudfront.net/flask-admin/localized.png
	:target: https://crowdin.com/project/flask-admin

.. image:: https://travis-ci.org/flask-admin/flask-admin.png?branch=master
	:target: https://travis-ci.org/flask-admin/flask-admin

Introduction
------------

Flask-Admin is a batteries-included, simple-to-use `Flask <http://flask.pocoo.org/>`_ extension that lets you
add admin interfaces to Flask applications. It is inspired by the *django-admin* package, but implemented in such
a way that the developer has total control of the look, feel and functionality of the resulting application.

Out-of-the-box, Flask-Admin plays nicely with various ORM's, including

- `SQLAlchemy <http://www.sqlalchemy.org/>`_,

- `MongoEngine <http://mongoengine.org/>`_,

- `pymongo <http://api.mongodb.org/python/current/>`_ and

- `Peewee <https://github.com/coleifer/peewee>`_.

It also boasts a simple file management interface and a `redis client <http://redis.io/>`_ console.

The biggest feature of Flask-Admin is flexibility. It aims to provide a set of simple tools that can be used for
building admin interfaces of any complexity. So, to start off with you can create a very simple application in no time,
with auto-generated CRUD-views for each of your models. But then you can go further and customize those views & forms
as the need arises.

Flask-Admin is an active project, well-tested and production ready.

Examples
--------
Several usage examples are included in the */examples* folder. Please feel free to add your own examples, or improve
on some of the existing ones, and then submit them via GitHub as a *pull-request*.

You can see some of these examples in action at `http://examples.flask-admin.org <http://examples.flask-admin.org/>`_.
To run the examples on your local environment, one at a time, do something like::

    cd flask-admin
    python examples/simple/app.py

Documentation
-------------
Flask-Admin is extensively documented, you can find all of the documentation at `http://flask-admin.readthedocs.org/en/latest/ <http://flask-admin.readthedocs.org/en/latest/>`_.

The docs are auto-generated from the *.rst* files in the */doc* folder. So if you come across any errors, or
if you think of anything else that should be included, then please make the changes and submit them as a *pull-request*.

To build the docs in your local environment::

    sudo pip install sphinx
    cd flask-admin
    sudo make html

Or, if you want to preview any *.rst* snippets that you may want to contribute, go to `http://rst.ninjs.org/ <http://rst.ninjs.org/>`_.

Installation
------------
To install Flask-Admin, simply::

    pip install flask-admin

Or alternatively, you can download the repository and install manually by doing::

    git clone git@github.com:flask-admin/flask-admin.git
    cd flask-admin
    python setup.py install

Tests
-----
Test are run with *nose*. If you are not familiar with this package you can get some more info from `their website <http://nose.readthedocs.org/>`_.

To run the tests, simply::

    pip install nose
    pip install -r dev-requirements.txt

and then::

    cd flask-admin
    nosetests

You should see output similar to::

    ...
    ----------------------------------------------------------------------
    Ran 41 tests in 2.092s

Please note that you will need to install some additional dependencies in order for all of the tests to be executed successfully.

3rd Party Stuff
---------------

Flask-Admin is built with the help of `Bootstrap <http://getbootstrap.com/>`_ and `Select2 <https://github.com/ivaynberg/select2>`_.

If you want to localize your application, install the `Flask-BabelEx <https://pypi.python.org/pypi/Flask-BabelEx>`_ package.

You can help improve Flask-Admin's translations through Crowdin: https://crowdin.com/project/flask-admin
