Flask-Admin
##############

**Why Flask?** As a micro-framework, `Flask <http://flask.pocoo.org/>`_ lets you build web services with very little overhead.
It offers freedom for you, the designer, to implement your project in a way that suits your
particular application.

**Why Flask-Admin?** In a world of micro-services and APIs, Flask-Admin solves
the really boring problem of letting you quickly build an admin interface on top
of an existing data model. With little effort, it makes it possible for
you to manage your web service's data through a user-friendly interface.

Examples
==========

Flask-Admin comes with several examples that will help you get a grip on what's possible.
Have a look at http://examples.flask-admin.org/ to see them in action, or browse through the `examples` directory in the GitHub repository.

****

Getting Started
=================

Flask-Admin lets you build complicated interfaces by grouping individual views
together in classes: Each web page you see on the frontend, represents a
method on a class that has explicitly been added to the interface.

These view classes are especially helpful when they are tied to particular
database models,
because they let you group together all of the usual
**Create, Read, Update, Delete** (CRUD) view logic into a single, self-contained
class for each of your models.

Initialization
--------------

To get started, the first step, is to initialise an empty admin interface on your Flask app::

    from flask import Flask
    from flask_admin import Admin

    app = Flask(__name__)

    admin = Admin(app, name='My App', template_mode='bootstrap3')
    # Add administrative views here

    app.run()

Here, both the *name* and *template_mode* parameters are optional.

If you start this application and navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see an empty page with a navigation bar on top.

Adding Model Views
----------------------

Model views allow you to add a dedicated set of admin pages for any model in your database. Do this by creating
instances of the *ModelView* class, which you can import from one of Flask-Admin's built-in ORM backends. An example
is the SQLAlchemy backend, which you can use as follows::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    admin = Admin(app)
    admin.add_view(ModelView(User, db.session))

Straight out of the box, this gives you a set of fully featured *CRUD* views for your model:

    * A `list` view, with support for searching, sorting and filtering and deleting records.
    * A `create` view for adding new records.
    * An `edit` view for updating existing records.

There are many options available for customizing the display and functionality of these builtin view.
For more details on that, see :ref:`customising-builtin-views`.

Adding Content to the Index Page
------------------------------------
The first thing you'll notice when you visit `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_
is that it's just an empty page with a navigation menu. To add some content to this page, save the following text as `admin/index.html` in your project's `templates` directory::

    {% extends 'admin/master.html' %}

    {% block body %}
      <p>Hello world</p>
    {% endblock %}

This will override the default index template, but still give you the navigation menu. So, now you can add any content to the index page that makes sense for your app.

****

Authorisation & Permissions
=================================
When setting up an admin interface for your application, one of the first problems
you'll want to solve is how to keep unwanted users out. With Flask-Admin there
are a few different ways of approaching this.

HTTP Basic Auth
------------------------
The simplest form of authentication is HTTP Basic Auth. It doesn't interfere
with your database models, and it doesn't require you to write any new view logic or
template code. So it's great for when you're deploying something that's still
under development, before you want the whole world to see it.

Have a look at `Flask-BasicAuth <http://flask-basicauth.readthedocs.org/>`_ to see just how
easy it is to put your whole application behind HTTP Basic Auth.

Unfortunately, there is no easy way of applying HTTP Basic Auth just to your admin
interface.

Rolling Your Own
--------------------------------
For a finer-grained solution, Flask-Admin lets you define access control rules
on each of your admin view classes by simply overriding the `is_accessible` method.
How you implement the logic is up to you, but if you were to use a low-level library like
`Flask-Login <https://flask-login.readthedocs.org/>`_, then restricting access
could be as simple as::

    class BaseModelView(sqla.ModelView):

        def is_accessible(self):
            return login.current_user.is_authenticated()

However, you would still need to implement all of the relevant login,
registration and account management views yourself.

For a basic example of this, have a look at https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth-flask-login.

Using Flask-Security
--------------------------------

If you want to get started quicker, you could
use `Flask-Security <https://pythonhosted.org/Flask-Security/>`_,
which is a higher-level library. It comes with lots of builtin views for doing
common things like user registration, login, email address confirmation, password resets, etc.

The only complicated bit, is making the builtin Flask-Security views integrate smoothly with the
Flask-Admin templates to create a consistent user experience. To
do this, you will need to override the builtin Flask-Security templates and have them
extend the Flask-Admin base template by adding the following to the top
of each file::

    {% extends 'admin/master.html' %}

Now, you'll need to manually pass in some context variables for the Flask Admin
templates to render correctly when they're being called from the Flask-Security views.
This could look something like::

    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
        )

For a working example of using Flask-Security with Flask-Admin, have a look at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth.

The example only uses the builtin `register` and `login` views, but you could follow the same
approach for including the other views, like `forgot_password`, `send_confirmation`, etc.

****

.. _customising-builtin-views:

Customising Builtin Views
=================================

The builtin `ModelView` class is great for getting started quickly. But you'll want
to configure its functionality
to suit your particular models. This is done by setting values for the configuration
attributes that are made available on the `ModelView` class.

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


`ModelView` Configuration Attributes
-----------------------------------

For a complete list of the attributes that are defined, have a look at the
API documentation for :meth:`~flask_admin.model.BaseModelView`. But, here follows
some of the most commonly used ones:

To disable some of the basic CRUD operations, set any of these boolean parameters::

    can_create = True
    can_edit = True
    can_delete = True


Configuring the List View
****************************

Removing some columns from the list view is easy, just use something like::

    column_exclude_list = ['password', ]

To make some of your columns searchable, or to use them for filtering, specify
a list of column names::

    column_searchable_list = ['name', 'email']
    column_filters = ['country', ]

For a faster editing experience, make some of the columns editable in the list view::

    column_editable_list = ['name', 'last_name']

Configuring the Create & Edit Views
************************************

You can restrict the possible values for a text-field by specifying a list of choices::

    form_choices = {
        'title': [
            ('MR', 'Mr'),
            ('MRS', 'Mrs'),
            ('MS', 'Ms'),
            ('DR', 'Dr'),
            ('PROF', 'Prof.')
        ]
    }

To remove some fields from the create and edit forms::

    form_excluded_columns = ['last_name', 'email']

To specify arguments to the WTForms fields when they are being rendered::

    form_args = {
        'name': {
            'label': 'First Name',
            'validators': [required()]
        }
    }

And, to go one level deeper, you can specify arguments to the widgets used to
render those fields::

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
            'fields': ['first_name', 'last_name', 'email']
            'page_size': 10
        }
    }

Changing the Look & Feel
---------------------------------

To take full control over the look & feel of the admin interface, you can override
all of the builtin templates. Just keep in mind that the templates will change slightly
from one Flask-Admin version to the next, so once you start overriding them, you
need to take care when upgrade your package version.

To override any of the builtin templates, simply copy them from
the Flask-Admin source into `templates/admin/` in your project directory.
As long as the filenames stay the same, the templates in your project directory should
automatically take precedence over the builtin ones.

If you want to keep your custom templates in some other location, then you need
to remember to reference them from the ModelView classes where you intend to
use them, for example::

    class BaseModelView(ModelView):
        list_template = 'base_list.html'
        create_template = 'base_create.html'
        edit_template = 'base_edit.html'

Have a look at the `layout` example at https://github.com/flask-admin/flask-admin/tree/master/examples/layout
to see how you can take full stylistic control over the admin interface.

Replacing Individual Form Fields
------------------------------------------

The `form_overrides` attribute allows you to replace individual fields within a form.
A comon use-case for this would be to add a rich text editor, or to handle
file / image uploads that need to be tied to a field in your model.

Rich-Text Fields
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
        form_overrides = {
            'body': CKTextAreaField
        }
        create_template = 'ckeditor.html'
        edit_template = 'ckeditor.html'

For this to work, you would also need to create a template that extends the default
functionality by including the necessary CKEditor javascript on the `create` and
`edit` pages. Save this in `templates/ckeditor.html`::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
      {{ super() }}
      <script src="http://cdnjs.cloudflare.com/ajax/libs/ckeditor/4.0.1/ckeditor.js"></script>
    {% endblock %}

File & Image Fields
*******************

Flask-Admin comes with a builtin `FileUploadField` and `ImageUploadField`. To make use
of them, you'll need to specify an upload directory, and add them to the forms in question.
Image handling also requires you to have `Pillow <https://pypi.python.org/pypi/Pillow/2.8.2>`_ installed.

Have a look a the example at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/forms.

If you just want to manage static files in a directory, without tying them to a database model, then
rather use the handy :ref:`File-Admin<file-admin>` plugin.

****

Adding Your Own Views
======================
For situations where your requirements are really specific, and you struggle to meet
them with the builtin :class:`~flask_admin.model.ModelView` class: Flask-Admin makes it easy for you to
take full control and add your own views to the interface.

Standalone Views
------------------
To add a set of standalone views, that are not tied to any particular model, you can extend the
:class:`~flask_admin.base.BaseView` class, and define your own view methods on it. For
example, to add a page that displays some analytics data from a 3rd-party API::

    from flask_admin import BaseView, expose

    class AnalyticsView(BaseView):
        @expose('/')
        def index(self):
            return self.render('analytics_index.html')

    admin.add_view(CustomView(name='Analytics'))

This will add a link to the navbar, from where your view can be accessed. Notice that
it is served at '/', the root URL. This is a restriction on standalone views: at the very minimum, each view class needs
at least one method, that serves a view at the root URL.

The `analytics_index.html` template for the example above, could look something like::

    {% extends 'admin/master.html' %}
    {% block body %}
      <p>Here I'm going to display some data.</p>
    {% endblock %}

By extending the *admin/master.html* template, you can maintain a consistent user experience,
even while having tight control over your page's content.

Overriding the Builtin Views
------------------------------------

There may be some scenarios where you want most of the builtin ModelView
functionality, but you want to replace one of the default `create`, `edit`, or `list` views.
For this you could override only the view in question, and all the links to it will still function as you would expect::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class UserView(ModelView):
    @expose('/new/', methods=('GET', 'POST'))
        def create_view(self):
        """
            Custom create view.
        """

        return self.render('create_user.html')


****

.. toctree::
   :maxdepth: 2

   advanced
   api/index

****

Support
----------

Python 2.6 - 2.7 and 3.3 - 3.4.

****

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
