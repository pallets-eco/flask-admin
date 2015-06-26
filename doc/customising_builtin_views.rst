.. _customising-builtin-views:

Customising Builtin Views
=================================

Image fields
---------------


HTML fields
---------------


List view options
-------------------


Form view options
-------------------


To customize these model views, you have two options: Either you can override the public properties of the *ModelView*
class, or you can override its methods.

For example, if you want to disable model creation and only show certain columns in the list view, you can do
something like::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class MyView(ModelView):
        # Disable model creation
        can_create = False

        # Override displayed fields
        column_list = ('login', 'email')

        def __init__(self, session, **kwargs):
            # You can pass name and other parameters if you want to
            super(MyView, self).__init__(User, session, **kwargs)

    admin = Admin(app)
    admin.add_view(MyView(db.session))

Overriding form elements can be a bit trickier, but it is still possible. Here's an example of
how to set up a form that includes a column named *status* that allows only predefined values and
therefore should use a *SelectField*::

    from wtforms.fields import SelectField

    class MyView(ModelView):
        form_overrides = dict(status=SelectField)
        form_args = dict(
            # Pass the choices to the `SelectField`
            status=dict(
                choices=[(0, 'waiting'), (1, 'in_progress'), (2, 'finished')]
            ))


It is relatively easy to add support for different database backends (Mongo, etc) by inheriting from
:class:`~flask_admin.model.BaseModelView`.
class and implementing database-related methods.

Please refer to :mod:`flask_admin.contrib.sqla` documentation on how to customize the behavior of model-based
administrative views.