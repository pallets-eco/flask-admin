.. _customising-builtin-views:

Customising Builtin Views
=================================

The builtin `ModelView` class is great for getting started quickly. But you'll want
to adapt it's functionality
to suit your particular models. To do this, there's a whole host of configuration
attributes that you can set either globally, or just for specific models.

To specify some global configuration parameters, you can subclass `ModelView`, and then use that
subclass when adding your models to the interface::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class BaseModelView(ModelView):
        can_delete = False  # disable model deletion
        page_size = 50  # the number of entries to display on the list view

    admin.add_view(BaseModelView(User, db.session))
    admin.add_view(BaseModelView(Post, db.session))

Or, in much the same way, you can specify options for a single model at a time::

    class UserView(ModelView):
            can_delete = False  # disable model deletion

    class PostView(ModelView):
            page_size = 50  # the number of entries to display on the list view

    admin.add_view(UserView(User, db.session))
    admin.add_view(PostView(Post, db.session))


View configuration attributes
-----------------------------

For a complete list of all the options that are available, have a look at the
API documentation for :meth:`~flask_admin.model.BaseModelView`. Here we are
just highlighting some of the most useful ones.

To disable some of the basic CRUD operations, set any of these boolean parameters::

    can_create = True
    can_edit = True
    can_delete = True


Common List view options
**************************

Removing some columns from the list view is easy, just use something like::

    column_exclude_list = ['password', ]

To make some of your columns searchable, or to use them for filtering, specify
a list of column names, e.g.::

    column_searchable_list = ['name', 'email']
    column_filters = ['country', ]

For a faster editing experience, make some of the columns editable in the list view::

    column_editable_list = ['name', 'last_name']

Common Form view options
**************************

You can restrict the values of a text-field by specifying a list of choices::

    form_choices = {
        'title': [
            ('MR', 'Mr'),
            ('MRS', 'Mrs'),
            ('MS', 'Ms'),
            ('DR', 'Dr'),
            ('PROF', 'Prof.')
        ]
    }

To remove some fields from the forms::

    form_excluded_columns = ('last_name', 'email')

To specify arguments for rendering the WTForms fields::

    form_args = {
        'name': {
            'label': 'First Name',
            'validators': [required()]
        }
    }

Or, to go one level deeper, you can specify arguments for the widgets used to
render those fields. For example::

    form_widget_args = {
        'description': {
            'rows': 10,
            'style': 'color: black'
        }
    }

To speed up page loading when you have forms with foreign keys, have those
related models loaded via ajax, using::

    form_ajax_refs = {
        'user': {
            'fields': ('first_name', 'last_name', 'email')
            'page_size': 10
        }
    }

Overriding the default templates
---------------------------------

To do this, find your flask-admin installation (this could be somewhere like `/env/lib/python2.7/site-packages/flask_admin/`
and copy the template in `templates/bootstrap3/admin/index.html` to your own project directory at `my_app/templates/admin/index.html`.



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

Replacing specific form fields
------------------------------------------

Individual form fields can be replaced completely by specifying the `form_overrides` attribute.
You can use this to add a rich text editor, or to handle
file / image uploads that need to be tied to a field in one of your models.

Rich-text fields
**********************
To handle complicated text content, use `CKEditor <http://ckeditor.com/>`_ by subclassing some of the builtin WTForms classes as follows::

    from wtforms import TextAreaField
    from wtforms.widgets import TextArea

    class CKTextAreaWidget(TextArea):
        def __call__(self, field, **kwargs):
            if kwargs.get('class'):
                kwargs['class'] += ' ckeditor'
            else:
                kwargs.setdefault('class', 'ckeditor')
            return super(CKTextAreaWidget, self).__call__(field, **kwargs)

    class CKTextAreaField(TextAreaField):
        widget = CKTextAreaWidget()

    class MessageAdmin(ModelView):
        form_overrides = dict(body=wtf.FileField)
        create_template = 'ckeditor.html'
        edit_template = 'ckeditor.html'

For this to work, you would also need to create a template that extends the default
functionality by including the necessary CKEditor javascript on the `create` and
`edit` pages. Save this in `templates/ckeditor.html::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
        {{ super() }}
        <script src="http://cdnjs.cloudflare.com/ajax/libs/ckeditor/4.0.1/ckeditor.js"></script>
    {% endblock %}

File & Image fields
*******************

For handling File & Image fields, have a look a the example at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/forms.

You'll need to specify an upload directory, and then use either `FileUploadField` or
`ImageUploadField` to override the field in question.

If you just want to manage static files, without tying them to a database model, then
rather use the :ref:`File-Admin<file-admin>` plugin.

