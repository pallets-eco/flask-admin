:tocdepth: 2

Flask-Admin
###########

**Why Flask?** As a micro-framework, `Flask <http://flask.pocoo.org/>`_ lets you build web services with very little overhead.
It offers freedom for you, the designer, to implement your project in a way that suits your
particular application.

**Why Flask-Admin?** In a world of micro-services and APIs, Flask-Admin solves
the boring problem of building an admin interface on top
of an existing data model. With little effort, it lets
you manage your web service's data through a user-friendly interface.

**How does it work?** The basic concept behind Flask-Admin, is that it lets you
build complicated interfaces by grouping individual views
together in classes: Each web page you see on the frontend, represents a
method on a class that has explicitly been added to the interface.

These view classes are especially helpful when they are tied to particular
database models,
because they let you group together all of the usual
*Create, Read, Update, Delete* (CRUD) view logic into a single, self-contained
class for each of your models.

**What does it look like?** Clone the `GitHub repository <https://github.com/flask-admin/flask-admin>`_
and run the provided examples locally to get a feel for Flask-Admin. There are several to choose from
in the `examples` directory.

.. toctree::
   :maxdepth: 2

   introduction
   advanced
   adding_a_new_model_backend
   api/index
   changelog

Support
-------

****

Python 2.7 and 3.3 or higher.

Indices And Tables
------------------

****

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
