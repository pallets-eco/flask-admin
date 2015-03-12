Usage Tips
==========

General tips
------------

 1. A reasonably obvious, but very useful, pattern is to wrap any shared functionality that your different admin views
    might need into a base class that they can all inherit from (to help you keep things
    `DRY <http://en.wikipedia.org/wiki/Don't_repeat_yourself>`_).

    For example, rather than manually checking user permissions in each of your admin views, you can implement a
    base class such as ::

        class MyView(BaseView):
            def is_accessible(self):
                return login.current_user.is_authenticated()

    and every view that inherits from this, will have the permission checking done automatically. The important thing
    to notice, is that your base class needs to inherit from a built-in Flask-Admin view.

 2. You can override a default template either by passing the path to your own template in to the relevant `ModelView`
    property (either `list_template`, `create_template` or `edit_template`) or by putting your own customized
    version of a default template into your `templates/admin/` directory.

 3. To customize the overall look and feel of the default model forms, you have two options: Either, you could
    override the default create/edit templates. Or, alternatively, you could make use of the form rendering rules
    (:mod:`flask_admin.form.rules`) that were introduced in version 1.0.7.

 4. To simplify the management of file uploads, Flask-Admin comes with a dedicated tool, for which you can find
    documentation at: :mod:`flask_admin.form.upload`.

 5. If you don't want to the use the built-in Flask-Admin form scaffolding logic, you are free to roll your own
    by simply overriding :meth:`~flask_admin.model.base.scaffold_form`. For example, if you use
    `WTForms-Alchemy <https://github.com/kvesteri/wtforms-alchemy>`_, you could put your form generation code
    into a `scaffold_form` method in your `ModelView` class.


SQLAlchemy
----------

1. If the `synonym_property` does not return a SQLAlchemy field, then Flask-Admin won't be able to figure out what to
   do with it, so it won't generate a form field. In this case, you would need to manually contribute your own field::

    class MyView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = TextField('Extra')
            return form_class

MongoEngine
-----------

1. Flask-Admin supports GridFS-backed image- and file uploads, done through WTForms fields. Documentation can be found
   at :mod:`flask.ext.admin.contrib.mongoengine.fields`.
