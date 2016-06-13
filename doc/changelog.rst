Changelog
=========

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
