Changelog
=========

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

1.2.0
-----

* Codebase was migrated to Flask-Admin GitHub organization
* Automatically inject Flask-WTF CSRF token to internal Flask-Admin forms
* MapBox v4 support for GeoAlchemy
* Updated translations with help of CrowdIn
* Show warning if field was ignored in form rendering rules
* Simple AppEngine backend
* Optional support for Font Awesome in templates and menus
* Bug fixes

1.1.0
-----

Mostly bug fix release. Highlights:

* Inline model editing on the list page
* FileAdmin refactoring and fixes
* FileUploadField and ImageUploadField will work with Required() validator
* Bug fixes


1.0.9
-----

Highlights:

* Bootstrap 3 support
* WTForms 2.x support
* Updated DateTime picker
* SQLAlchemy backend: support for complex sortables, ability to search for related models, model inheritance support
* Customizable URL generation logic for all views
* New generic filter types: in list, empty, date range
* Added the ``geoa`` contrib module, for working with `geoalchemy2 <http://geoalchemy-2.readthedocs.org/>`_
* Portugese translation
* Lots of bug fixes
