MongoEngine backend
===================

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

MongoEngine integration example is `here <https://github.com/flask-admin/flask-admin/tree/master/examples/mongoengine>`_.
