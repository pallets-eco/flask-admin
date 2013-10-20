Form rendering rules
--------------------

Before version 1.0.7, all model backends were rendering the creation and editing forms
using the special Jinja2 macro, which was looping over WTForms form object fields and displaying
them one by one.

Starting from version 1.0.7, Flask-Admin supports so called form rendering rules.

Idea is pretty simple: instead of having non-configurable macro that renders the form,
have a set of rules that tell Flask-Admin how form should be rendered. As an extension
of the idea, rules can output HTML, call Jinja2 macros, render fields and so on.

Essentially, form rendering rules abstract form rendering away from the form definition. And it
no longer matters what is sequence of the fields in the form.

Getting started
---------------

To start using form rendering rules, you need to put list of form field names into `form_create_rules`
property of your administrative view::

	class RuleView(sqla.ModelView):
	    form_create_rules = ('email', 'first_name', 'last_name')

In this example, only three fields will be rendered and `email` field will be above other two fields.

Whenever Flask-Admin sees string as a value in `form_create_rules`, it automatically assumes that it is
form field reference and created :class:`flask.ext.admin.form.rules.Field` class instance.

Lets say we want to display 'Foobar' text between `email` and `first_name` fields. This can be accomplished by
using :class:`flask.ext.admin.form.rules.Text` class::

	from flask.ext.admin.form import rules

	class RuleView(sqla.ModelView):
	    form_create_rules = ('email', rules.Text('Foobar'), 'first_name', 'last_name')

Flask-Admin comes with few built-in rules that can be found in :mod:`flask.ext.admin.form.rules` module:

======================================================= ========================================================
:class:`flask.ext.admin.form.rules.BaseRule`            All rules derive from this class
:class:`flask.ext.admin.form.rules.NestedRule`          Allows rule nesting, useful for HTML containers
:class:`flask.ext.admin.form.rules.Text`                Simple text rendering rule
:class:`flask.ext.admin.form.rules.HTML`                Same as `Text` rule, but does not escape the text
:class:`flask.ext.admin.form.rules.Macro`               Calls macro from current Jinja2 context
:class:`flask.ext.admin.form.rules.Container`           Wraps child rules into container rendered by macro
:class:`flask.ext.admin.form.rules.Field`               Renders single form field
:class:`flask.ext.admin.form.rules.Header`              Renders form header
:class:`flask.ext.admin.form.rules.FieldSet`            Renders form header and child rules
======================================================= ========================================================

For additional documentation, check :mod:`flask.ext.admin.form.rules` module source code (it is quite short) and
look at the `forms` example.
