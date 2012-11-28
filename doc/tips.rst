Usage Tips
==========

General tips
------------

1. Use class inheritance. If your models share common functionality,
create base class which will be responsible for this functionality.

For example - permissions. Don't implement `is_accessible` in  every administrative view. Create your own base class,
implement is_accessible there and use it instead.

2. You can override templates either by using `ModelView` properties or
putting customized version into your `templates/admin/` directory


SQLAlchemy
----------

1. If `synonym_property` does not return SQLAlchemy field, Flask-Admin
won't be able to figure out what to do with it and won't generate form
field. In this case, you need to manually contribute field::

    class MyView(ModelView):
        def scaffold_form(self):
            form_class = super(UserView, self).scaffold_form()
            form_class.extra = wtf.TextField('Extra')
            return form_class
