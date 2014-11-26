Changelog
=========

1.1 (dev)
---------

Highlights:

* Added the ``geoa`` contrib module, for working with `geoalchemy2`_

.. _geoalchemy2: http://geoalchemy-2.readthedocs.org/

1.0.8
-----

Highlights:

* Cleaned up documentation, many thanks to Petrus Janse van Rensburg.
* More flexible menu system, ability to add links to menus
* Human-readable filter URLs
* Callable filter `options`
* `EmailField` filter
* Simple accessibility fixes
* `InlineFormField` now accepts `widget_args` and `form_rules` arguments
* Support for newer wtforms versions
* `form_rules` property that affects both create and edit forms
* Lots of bugfixes

1.0.7
-----

Full change log and feature walkthrough can be found `here <http://mrjoes.github.io/2013/10/21/flask-admin-107.html>`_.

Highlights:

* Python 3 support
* AJAX-based foreign-key data loading for all backends
* New, optional, rule-based form rendering engine
* MongoEngine fixes and features: GridFS support, nested subdocument configuration and much more
* Greatly improved and more configurable inline models
* New WTForms fields and widgets
* `form_extra_columns` allows adding custom columns to the form declaratively
* Redis cli
* SQLAlchemy backend can handle inherited models with multiple PKs
* Lots of bug fixes

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
* Translations: French, Persian (Farsi), Chinese (Simplified/Traditional), Czech
* Bug fixes
