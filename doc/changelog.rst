Changelog
=========

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
