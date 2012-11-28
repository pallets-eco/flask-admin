Changelog
=========

1.0.4
-----

* MongoEngine support
* Raw PyMongo support
* Model property names are more consistent now
* Revamped InlineForm implementation
* Proper support of SQLAlchemy model inheritance
* Updated to bootstrap 2.2.1

1.0.3
-----

General:

* Peewee 2.x support
* Model form scaffolding is now customizable in model views
* Inline model forms are much more customizable now
* List view type-based formatters
* Database ``NULL`` will be displayed in list view as empty string by default. Use type-based formatter if you want to show something else.
* `Use Select2 <http://ivaynberg.github.com/select2/>`_ instead of Chosen
* List view formatting callbacks. See `example <https://gist.github.com/3714266>`_.
* ``_template_args`` property is now available in all views
* ``on_model_change`` and ``on_model_delete`` callbacks
* Model backends now support ``list_display_pk`` property
* Minor template refactoring, more blocks to override
* Supported multiple ``Admin`` class instances for one Flask application
* File uploads are now supported in model views
* Use HTTPS CDN for jQuery
* Lots of minor fixes

SQLAlchemy backend:

* Support for non-nullable boolean fields
* If create/delete/update fails, Flask-Admin will rollback the transaction
* Default column values support
* ``list_display_all_relations`` to show many-to-one relations in list view
* ``get_query`` method, which can be overridden to implement additional filtering/sorting/etc
* Synonym properties support
* Backend will ignore protected fields (name starting with underscore) from now on
* Support for various PostgreSQL fields

1.0.2
-----

* Peewee model backend
* Inline form administration interface for models a-la Django
* Mass actions - methods that work with more than one item (for example - mass delete for models or files)
* SQLAlchemy form scaffolding is now independent from the wtforms.ext.sqlalchemy helpers
* Added ability to mount administrative interface as a top-level folder
* Administrative interface can now be mounted as a subdomain
* Can now use FileField in model admin
* Revamped model templates, much more customizable now
* Model list view column formatting callbacks
* Lots of bugfixes

1.0.1
-----

* Fixed setup manifest


1.0.0
-----

* Initial release