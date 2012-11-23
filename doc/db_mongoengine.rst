MongoEngine backend
===================

Features:

 - MongoEngine 0.7+ support;
 - Paging, sorting, filters, etc;
 - Inline editing of related models;

In order to use MongoEngine integration, you need to install `flask-mongoengine` package,
as Flask-Admin uses form scaffolding from it.

You don't have to use Flask-MongoEngine in your project - Flask-Admin will work with "raw"
MongoEngine models without any problems.

Known issues:

 - There's no way to configure EmbeddedDocument display options
 - Search functionality can't split query into multiple terms


For more documentation, check :doc:`api/mod_contrib_mongoengine` documentation.
