Changelog
=========

1.0.6
-----

* Model views now support default sorting order
* Model type/column formatters now accept additional `view` parameter
* `is_visible` for administrative views
* Model views have `after_model_change` method that can be overridden
* In model views, `get_query` was split into `get_count_query` and `get_query`
* Bootstrap 2.3.1
* Bulk deletes go through `delete_model`
* Flask-Admin no longer uses floating navigation bar
* Translations: French, Persian (Farsi), Chinese (Simplified/Traditional), Chech
* Bug fixes

1.0.5
-----

* SQLAlchemy 0.8 support
* Choices and PostgreSQL Enum field type support
* Flask-BabelEx will be used to localize administrative interface
* Simple text file editor
* File admin has additional hooks: rename, edit, upload, etc
* Simple text file editor
* External links in menu
* Column descriptions
* Possibility to override master template
* Reworked templates. New 'layout' sample with completely different administrative UI
* Ability to customize wtforms widget rendering through `form_widget_args` property
* German translation (WIP)
* Updated documentation
* Lots of bug fixes


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
