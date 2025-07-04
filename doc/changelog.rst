Changelog
=========

2.0.0a4
-------
Breaking changes:

* Azure Blob Storage SDK has been upgraded from the legacy version (v2) to the latest version (v12). AzureFileAdmin now accept `blob_service_client` rather than `connection_string` to give more flexibility with connection types.

2.0.0a3
-------

Fixes:

* Jinja templates can now be loaded in StrictUndefined mode.
* Remove an implicit dependency on `packaging`
* Fixed an error caused by the fallback implementation of `gettext()` (when used in templates)

2.0.0a2
-------

Breaking changes:

* Removed support for Python 3.8.
* Use of the `boto` library has been replaced by `boto3`. S3FileAdmin and S3Storage now accept an `s3_client` parameter taking a `boto3.client('s3')` instance rather than `aws_access_key_id`, `aws_secret_access_key`, and `region` parameters.

2.0.0a1
-------

Fixes:

* Fixes compatibility with WTForms 3.2+.
* The `Apply` button for filters will show/hide correctly again
* Fix `translations_path` attribute when Flask-Admin is used with Flask-Babel
* Some translation updates.
* Date fields no longer override `widget` if set in `form_args`
* “Save and Continue Editing” button no longer discards the “return URL” (allowing to retain filters when switching back to the list)

2.0.0a0
-------

Breaking changes:

* Added support for Python 3.12
* Dropped support for Python 3.7
* Flask-BabelEx is no longer supported; the package is no longer maintained and Flask-Babel is recommended/active instead.
* Flask-Mongoengine is no longer supported due to that package being unmaintained.
* Bootstrap2 and Bootstrap3 themes are no longer available.
* `Admin()` now takes a `theme` parameter that encapsulates all of the configuration options for theming the admin instance. This replaces the `template_mode` parameter.
* All remaining Flask-Admin config has been namespaced under `FLASK_ADMIN_`.

.. list-table:: Title
   :widths: 50 50
   :header-rows: 1

   * - Config variable name
     - What's changed
   * - FLASK_ADMIN_SWATCH
     - Removed; use `Theme(swatch=...)` instead
   * - FLASK_ADMIN_FLUID_LAYOUT
     - Removed; use `Theme(fluid=...)` instead
   * - MAPBOX_MAP_ID
     - Renamed to FLASK_ADMIN_MAPBOX_MAP_ID
   * - MAPBOX_SEARCH
     - Renamed to FLASK_ADMIN_MAPBOX_SEARCH
   * - MAPBOX_ACCESS_TOKEN
     - Renamed to FLASK_ADMIN_MAPBOX_ACCESS_TOKEN
   * - GOOGLE_MAPS_API_KEY
     - Renamed to FLASK_ADMIN_GOOGLE_MAPS_API_KEY
   * - DEFAULT_CENTER_LAT
     - Renamed to FLASK_ADMIN_DEFAULT_CENTER_LAT
   * - DEFAULT_CENTER_LONG
     - Renamed to FLASK_ADMIN_DEFAULT_CENTER_LONG
   * - ADMIN_RAISE_ON_INTEGRITY_ERROR
     - Renamed to FLASK_ADMIN_RAISE_ON_INTEGRITY_ERROR
   * - ADMIN_RAISE_ON_VIEW_EXCEPTION
     - Renamed to FLASK_ADMIN_RAISE_ON_VIEW_EXCEPTION

New features:

* Flask-Admin now supports the `host_matching` mode of Flask apps. See documentation for how to configure this where needed.
* Flask-Admin is now compatible with SQLAlchemy v2+, Flask v3+, WTForms v3+, and Pillow v10+.
* Flask-Admin now declares its dependencies and supported dependency versions more cleanly, including using pip extras. If you use Flask-Admin with SQLAlchemy, for example, you should use `pip install flask-admin[sqlalchemy]` or list `flask-admin[sqlalchemy]` in your requirements.txt or pyproject.toml files.
* Apps using content security policies to restrict the assets that can be loaded can now whitelist Flask-Admin's assets by passing a `csp_nonce_generator` function to the Admin instance. See examples or documentation for how to configure this where needed.
* `page_size_options` can now be configured on Admin models, to restrict the page sizes that users can select. These are now enforced properly and cannot be bypassed by URL hacking.

And various smaller bug fixes and documentation updates.

For the full changelog, see https://github.com/pallets-eco/flask-admin/releases/tag/v2.0.0a0

1.6.1
-----

* SQLAlchemy 2.x support
* General updates and bug fixes
* Dropped WTForms 1 support

1.6.0
-----

* Dropped Python 2 support
* WTForms 3.0 support
* Various fixes

1.5.8
-----

* SQLAlchemy 1.4.5+ compatibility fixes
* Redis CLI fixes

1.5.7
-----

* Bootstrap 4 support!
* Added hook for custom SQLAlchemy models initializers
* SQLAlchemy 1.4/2.0 compatibility fix

1.5.6
-----

* SQLAlchemy 1.3.6 compatibility fix
* Python 3.8 support

1.5.5
-----

* Werkzeug 1.0 compatibility fix
* Use fa-circle-o icon for unchecked booleans
* A few SQLAlchemy-related bug fixes

1.5.4
-----

* Fix display of inline x-editable boolean fields on list view
* Add support for several SQLAlchemy-Utils data types
* Support searching on SQLAlchemy hybrid properties
* Extra URL paramaters are now propagated to the next page when searching / filtering
* Add enum34 dependency when running on legacy Python version
* Update Mapbox API v1 URL format
* Update jQuery and moment dependencies in templates
* Fixed a datepicker issue, where only dates up to 2015 were showing up
* Updated Pillow dependency version

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
