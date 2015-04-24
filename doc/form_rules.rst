Form rendering rules
====================

Before version 1.0.7, all model backends were rendering the *create* and *edit* forms
using a special Jinja2 macro, which was looping over the fields of a WTForms form object and displaying
them one by one. This works well, but it is difficult to customize.

Starting from version 1.0.7, Flask-Admin supports form rendering rules, to give you fine grained control of how
the forms for your modules should be displayed.

The basic idea is pretty simple: the customizable rendering rules replace a static macro, so that you can tell
Flask-Admin how each form should be rendered. As an extension, however, the rendering rules also let you do a
bit more: You can use them to output HTML, call Jinja2 macros, render fields and so on.

Essentially, form rendering rules abstract the rendering, so that it becomes separate from the form definition. So,
for example, it no longer matters in which sequence your form fields are defined.

Getting started
---------------

To start using the form rendering rules, put a list of form field names into the `form_create_rules`
property one of your admin views::

    class RuleView(sqla.ModelView):
        form_create_rules = ('email', 'first_name', 'last_name')

In this example, only three fields will be rendered and `email` field will be above other two fields.

Whenever Flask-Admin sees a string value in `form_create_rules`, it automatically assumes that it is a
form field reference and creates a :class:`flask_admin.form.rules.Field` class instance for that field.

Lets say we want to display some text between the `email` and `first_name` fields. This can be accomplished by
using the :class:`flask_admin.form.rules.Text` class::

    from flask_admin.form import rules

    class RuleView(sqla.ModelView):
        form_create_rules = ('email', rules.Text('Foobar'), 'first_name', 'last_name')

Built-in rules
--------------

Flask-Admin comes with few built-in rules that can be found in the :mod:`flask_admin.form.rules` module:

======================================================= ========================================================
Form Rendering Rule                                     Description
======================================================= ========================================================
:class:`flask_admin.form.rules.BaseRule`                All rules derive from this class
:class:`flask_admin.form.rules.NestedRule`              Allows rule nesting, useful for HTML containers
:class:`flask_admin.form.rules.Text`                    Simple text rendering rule
:class:`flask_admin.form.rules.HTML`                    Same as `Text` rule, but does not escape the text
:class:`flask_admin.form.rules.Macro`                   Calls macro from current Jinja2 context
:class:`flask_admin.form.rules.Container`               Wraps child rules into container rendered by macro
:class:`flask_admin.form.rules.Field`                   Renders single form field
:class:`flask_admin.form.rules.Header`                  Renders form header
:class:`flask_admin.form.rules.FieldSet`                Renders form header and child rules
======================================================= ========================================================

Enabling CSRF Validation
------------------------
Adding CSRF validation will require overriding the :class:`flask_admin.form.BaseForm` by using :attr:`flask_admin.model.BaseModelView.form_base_class`.

WTForms >=2::

    from wtforms.csrf.session import SessionCSRF
    from wtforms.meta import DefaultMeta
    from flask import session
    from datetime import timedelta
    from flask_admin import form
    from flask_admin.contrib import sqla

    class SecureForm(form.BaseForm):
        class Meta(DefaultMeta):
            csrf = True
            csrf_class = SessionCSRF
            csrf_secret = b'EPj00jpfj8Gx1SjnyLxwBBSQfnQ9DJYe0Ym'
            csrf_time_limit = timedelta(minutes=20)

            @property
            def csrf_context(self):
                return session

    class ModelAdmin(sqla.ModelView):
        form_base_class = SecureForm

For WTForms 1, you can use use Flask-WTF's Form class::

    import os
    import flask
    import flask_wtf
    import flask_admin
    import flask_sqlalchemy
    from flask_admin.contrib.sqla import ModelView

    DBFILE = 'app.db'

    app = flask.Flask(__name__)
    app.config['SECRET_KEY'] = 'Dnit7qz7mfcP0YuelDrF8vLFvk0snhwP'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DBFILE
    app.config['CSRF_ENABLED'] = True

    flask_wtf.CsrfProtect(app)
    db = flask_sqlalchemy.SQLAlchemy(app)
    admin = flask_admin.Admin(app, name='Admin')

    class MyModelView(ModelView):
        # Here is the fix:
        form_base_class = flask_wtf.Form

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String)
        password = db.Column(db.String)

    if not os.path.exists(DBFILE):
        db.create_all()

    admin.add_view( MyModelView(User, db.session, name='User') )

    app.run(debug=True)

Further reading
---------------

For additional documentation, check :mod:`flask_admin.form.rules` module source code (it is quite short) and
look at the `forms example <https://github.com/flask-admin/flask-admin/tree/master/examples/forms>`_ on GitHub.
