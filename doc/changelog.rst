Changelog
=========

1.0.7
-----

Full change log and feature walkthrough can be found `here <http://mrjoes.github.com/TBD>`_.

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
