Usage Tips
==========

General tips
------------

1. Whenever your administrative views share common functionality such as authentication,
form validation, make use of read-only views and so on - create your own base class which
inherits from proper Flask-Admin view class.

For example, if you need to check user permissions for every call, don't implement
`is_accessible` in  every administrative view. Create your own base class, implement
`is_accessible` there and use this class for all your views.

2. You can override used templates either by using `ModelView` properties (such as
`list_template`, `create_template`, `edit_template`) or
putting customized version of the template into your `templates/admin/` directory

3. If you need to customize look and feel of model forms, there are two options:

  - Override create/edit template
  - Use new :mod:`flask.ext.admin.form.rules` form rendering rules

4. Flask-Admin has that manage file/image uploads and store result in model field. You can
find documentation here - :mod:`flask.ext.admin.form.upload`.


SQLAlchemy
----------

1. If `synonym_property` does not return SQLAlchemy field, Flask-Admin
won't be able to figure out what to do with it and won't generate form
field. In this case, you need to manually contribute field::

    class MyView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = TextField('Extra')
            return form_class

MongoEngine
-----------

1. Flask-Admin supports GridFS backed image and file uploads. Done through
WTForms fields and documentation can be found here :mod:`flask.ext.admin.contrib.mongoengine.fields`.
