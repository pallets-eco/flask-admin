Flask-Admin
===========

.. image:: https://travis-ci.org/mrjoes/flask-admin.png?branch=master
	:target: https://travis-ci.org/mrjoes/flask-admin

Introduction
------------

Flask-Admin is advanced, extensible and simple to use administrative interface building extension for the Flask framework.

It comes with batteries included: model scaffolding for `SQLAlchemy <http://www.sqlalchemy.org/>`_,
`MongoEngine <http://mongoengine.org/>`_, `pymongo <http://api.mongodb.org/python/current/>`_ and `Peewee <https://github.com/coleifer/peewee>`_ ORMs, simple
file management interface, redis client console and a lot of usage examples.

You're not limited by the default functionality - instead of providing simple scaffolding for the ORM
models, Flask-Admin provides tools that can be used to build administrative interface of any complexity,
using a consistent look and feel. Flask-Admin architecture is very flexible, there's no need to monkey-patch 
anything, every single aspect of the library can be customized.

Flask-Admin is evolving project, extensively tested and production ready.

Installation
------------
To install Flask-Admin, simply::

    pip install flask-admin

Or alternatively, you can download the repository and install manually by doing::

    cd flask-admin
    python setup.py install

Tests
-----
Test are run with *nose*. If you are not familiar with this package you can get some more info from `their website <http://nose.readthedocs.org/`_.

To run the tests, simply

    pip install nose

and then

    cd flask-admin
    nosetests

You should see output such as:

    ----------------------------------------------------------------------
    Ran 41 tests in 2.092s

Please note that you will need to install some additional dependencies in order for all of the tests to be executed successfully.


Documentation
-------------

Flask-Admin is extensively documented, you can find `documentation here <http://readthedocs.org/docs/flask-admin>`_.

3rd Party Stuff
---------------

Flask-Admin is built with the help of `Twitter Bootstrap <http://twitter.github.com/bootstrap/>`_ and `Select2 <https://github.com/ivaynberg/select2>`_.

If you want to localize administrative interface, install `Flask-BabelEx <https://pypi.python.org/pypi/Flask-BabelEx>`_ package.

Examples
--------

The library comes with a quite a few examples, you can find them in the `examples <https://github.com/mrjoes/flask-admin/tree/master/examples>`_ directory.
