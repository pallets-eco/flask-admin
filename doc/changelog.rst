Changelog
=========

Next release
-----

* Fix display of inline x-editable boolean fields on list view
* Add support for several SQLAlchemy-Utils data types
* Support searching on SQLAlchemy hybrid properties
* Extra URL paramaters are now propagated to the next page when searching / filtering
* Add enum34 dependency when running on legacy Python version
* Update Mapbox API v1 URL format
* Update jQuery and moment dependencies in templates
* Fixed a datepicker issue, where only dates up to 2015 were showing up

1.5.3
-----

* Fixed XSS vulnerability
* Support nested categories in the navbar menu
* SQLAlchemy
    * sort on multiple columns with `column_default_sort`
    * sort on related models in `column_sortable_list`
    * show searchable fields in search input's placeholder text
    * fix: inline model forms can now also be used for models with multiple primary keys
    * support for using mapped `column_property`
* Upgrade Leaflet and Leaflet.draw plugins, used for geoalchemy integration
* Specify `minimum_input_length` for ajax widget
* Peewee: support composite keys
* MongoEngine: when searching/filtering the input is now regarded as case-insensitive by default
* FileAdmin
    * handle special characters in filename
    * fix a bug with listing directories on Windows
    * avoid raising an exception when unknown sort parameter is encountered
* WTForms 3 support

1.5.2
-----

* Fixed XSS vulnerability
* Fixed Peewee support
* Added detail view column formatters
* Updated Flask-Login example to work with the newer version of the library
* Various SQLAlchemy-related fixes
* Various Windows related fixes for the file admin

1.5.1
-----

* Dropped Python 2.6 support
* Fixed SQLAlchemy >= 1.2 compatibility
* Fixed Pewee 3.0 compatibility
* Fixed max year for a combo date inline editor
* Lots of small bug fixes

1.5.0
-----

* Fixed CSRF generation logic for multi-process deployments
* Added WTForms >= 3.0 support
* Flask-Admin would not recursively save inline models, allowing arbitrary nesting
* Added configuration properties that allow injection of additional CSS and JS dependencies into templates without overriding them
* SQLAlchemy backend
  - Updated hybrid property detection using new SQLAlchemy APIs
  - Added support for association proxies
  - Added support for remote hybrid properties filters
  - Added support for ARRAY column type
* Localization-related fixes
* MongoEngine backend is now properly formats model labels
* Improved Google App Engine support:
  - Added TextProperty, KeyProperty and SelectField support
  - Added support for form_args, excluded_columns, page_size and after_model_update
* Fixed URL generation with localized named filters
* FileAdmin has Bootstrap 2 support now
* Geoalchemy fixes
  - Use Google Places (by default) for place search
* Updated translations
* Bug fixes

1.4.2
-----
* Small bug fix release. Fixes regression that prevented usage of "virtual" columns with a custom formatter.

1.4.1
-----

* Official Python 3.5 support
* Customizable row actions
* Tablib support (exporting to XLS, XLSX, CSV, etc)
* Updated external dependencies (jQuery, x-editable, etc)
* Added settings that allows exceptions to be raised on view errors
* Bug fixes

1.4.0
-----

* Updated and reworked documentation
* FileAdmin went through minor refactoring and now supports remote file systems. Comes with the new, optional, AWS S3 file management interface
* Configurable CSV export for model views
* Added overridable URL generation logic. Allows using custom URLs with parameters for administrative views
* Added column_display_actions to ModelView control visibility of the action column without overriding the template
* Added support for the latest MongoEngine
* New SecureForm base class for easier CSRF validation
* Lots of translation-related fixes and updated translations
* Bug fixes

1.3.0
-----

* New feature: Edit models in the list view in a popup
* New feature: Read-only model details view
* Fixed XSS in column_editable_list values
* Improved navigation consistency in model create and edit views
* Ability to choose page size in model list view
* Updated client-side dependencies (jQuery, Select2, etc)
* Updated documentation and examples
* Updated translations
* Bug fixes
