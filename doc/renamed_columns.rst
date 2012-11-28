Renamed Columns
---------------

Starting from version 1.0.4, Flask-Admin uses different configuration
property names.

Please update your sources as support for old property names will be
removed in future Flask-Admin versions.

=========================== =============================
**Old Name**                **New name**
--------------------------- -----------------------------
list_columns                column_list
excluded_list_columns       column_exclude_list
list_formatters             column_formatters
list_type_formatters        column_type_formatters
rename_columns              column_labels
sortable_columns            column_sortable_list
searchable_columns          column_searchable_list
list_display_pk             column_display_pk
hide_backrefs               column_hide_backrefs
auto_select_related         column_auto_select_related
list_select_related         column_select_related_list
list_display_all_relations  column_display_all_relations
excluded_form_columns       form_excluded_columns
disallowed_actions          action_disallowed_list
=========================== =============================
