Flask-Admin
##############

**Why Flask?** As a micro-framework, `Flask <http://flask.pocoo.org/>`_ lets you build web services with very little overhead.
It offers freedom for you, the designer, to implement your project in a way that suits your
particular application.

**Why Flask-Admin?** In a world of micro-services and APIs, Flask-Admin solves
the boring problem of building an admin interface on top
of an existing data model. With little effort, it lets
you manage your web service's data through a user-friendly interface.

**How does it work?** The basic concept behind Flask-Admin, is that it lets you
build complicated interfaces by grouping individual views
together in classes: Each web page you see on the frontend, represents a
method on a class that has explicitly been added to the interface.

These view classes are especially helpful when they are tied to particular
database models,
because they let you group together all of the usual
*Create, Read, Update, Delete* (CRUD) view logic into a single, self-contained
class for each of your models.

**What does it look like?** Have a look at http://examples.flask-admin.org/ to see
some examples of Flask-Admin in action, or browse through the `examples/`
directory in the `GitHub repository <https://github.com/flask-admin/flask-admin>`_.


.. toctree::
   :maxdepth: 2

   Index <index>

Getting Started
================

****

Initialization
-------------------

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

Model views allow you to add a dedicated set of admin pages for managing any model in your database. Do this by creating
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

There are many options available for customizing the display and functionality of these builtin views.
For more details on that, see :ref:`customising-builtin-views`. For more details on the other
ORM backends that are available, see :ref:`database-backends`.

Adding Content to the Index Page
------------------------------------
The first thing you'll notice when you visit `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_
is that it's just an empty page with a navigation menu. To add some content to this page, save the following text as `admin/index.html` in your project's `templates` directory::

    {% extends 'admin/master.html' %}

    {% block body %}
      <p>Hello world</p>
    {% endblock %}

This will override the default index template, but still give you the builtin navigation menu.
So, now you can add any content to the index page, while maintaining a consistent user experience.

Authorisation & Permissions
=================================

****

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
For a more flexible solution, Flask-Admin lets you define access control rules
on each of your admin view classes by simply overriding the `is_accessible` method.
How you implement the logic is up to you, but if you were to use a low-level library like
`Flask-Login <https://flask-login.readthedocs.org/>`_, then restricting access
could be as simple as::

    class BaseModelView(sqla.ModelView):

        def is_accessible(self):
            return login.current_user.is_authenticated()

        def _handle_view(self, name, **kwargs):
            if not self.is_accessible():
                return redirect(url_for('login', next=request.url))

Components that are not accessible to a particular user, will not be displayed
in the navigation menu for that user. But, you would still need to implement all of the relevant login,
registration and account management views yourself.

For an example of this, have a look at https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth-flask-login.

Using Flask-Security
--------------------------------

If you want a more polished solution, you could
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
Defining a `security_context_processor` function will take care of this for you::

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

.. _customising-builtin-views:

Customising Builtin Views
=================================

****

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
-------------------------------------

For a complete list of the attributes that are defined, have a look at the
API documentation for :meth:`~flask_admin.model.BaseModelView`. Here follows
some of the most commonly used ones:

To disable some of the basic CRUD operations, set any of these boolean parameters::

    can_create = True
    can_edit = True
    can_delete = True

Removing some columns from the list view is easy, just use something like::

    column_exclude_list = ['password', ]

To make some of your columns searchable, or to use them for filtering, specify
a list of column names::

    column_searchable_list = ['name', 'email']
    column_filters = ['country', ]

For a faster editing experience, make some of the columns editable in the list view::

    column_editable_list = ['name', 'last_name']

Or, have the edit form display inside a modal window on the list page, in stead of
on the dedicated *edit* page::

    edit_modal = True

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

Adding Your Own Views
======================

****

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




Working with the builtin templates
====================================

****

To take full control over the style and layout of the admin interface, you can override
all of the builtin templates. Just keep in mind that the templates will change slightly
from one version of Flask-Admin to the next, so once you start overriding them, you
need to take care when upgrading your package version.

To override any of the builtin templates, simply copy them from
the Flask-Admin source into your project's `templates/admin/` directory.
As long as the filenames stay the same, the templates in your project directory should
automatically take precedence over the builtin ones.

Have a look at the `layout` example at https://github.com/flask-admin/flask-admin/tree/master/examples/layout
to see how you can take full stylistic control over the admin interface.

See :ref:`extending-builtin-templates`.
To explore some more of what Jinja2 can offer you, head over to the
`Jinja2 docs <http://jinja.pocoo.org/docs/>`_.


Available Template Blocks
----------------------------

Flask-Admin defines one *base* template at `admin/master.html` that all the other admin templates are derived
from. This template is a proxy which points to `admin/base.html`, which defines
the following blocks:

============== ========================================================================
Block Name     Description
============== ========================================================================
head_meta      Page metadata in the header
title          Page title
head_css       Various CSS includes in the header
head           Empty block in HTML head, in case you want to put something  there
page_body      Page layout
brand          Logo in the menu bar
main_menu      Main menu
menu_links     Links menu
access_control Section to the right of the menu (can be used to add login/logout buttons)
messages       Alerts and various messages
body           Content (that's where your view will be displayed)
tail           Empty area below content
============== ========================================================================

In addition to all of the blocks that are inherited from `admin/master.html`, the `admin/model/list.html` template
also contains the following blocks:

======================= ============================================
Block Name              Description
======================= ============================================
model_menu_bar          Menu bar
model_list_table  		Table container
list_header       		Table header row
list_row_actions_header Actions header
list_row                Single row
list_row_actions        Row action cell with edit/remove/etc buttons
empty_list_message      Message that will be displayed if there are no models found
======================= ============================================

Environment variables
---------------------

While working in any of the templates that extend `admin/master.html`, you have access to a small number of
environment variables:

==================== ================================
Variable Name        Description
==================== ================================
admin_view           Current administrative view
admin_base_template  Base template name
_gettext             Babel gettext
_ngettext            Babel ngettext
h                    Helpers from :mod:`~flask_admin.helpers` module
==================== ================================


Customizing templates
---------------------

As noted earlier, you can override any default Flask-Admin template by creating your own template with same name and
relative path inside your own `templates` directory.

You can also override the master template, but then you need to pass your own template name to the `Admin`
constructor::

    admin = Admin(app, base_template='my_master.html')

****

Generating URLs
------------------

Internally, view classes work on top of Flask blueprints, so you can use *url_for* with a dot
prefix to get the URL for a local view::

    from flask import url_for

    class MyView(BaseView):
        @expose('/')
        def index(self)
            # Get URL for the test view method
            url = url_for('.test')
            return self.render('index.html', url=url)

        @expose('/test/')
        def test(self):
            return self.render('test.html')

If you want to generate a URL for a particular view method from outside, the following rules apply:

1. You can override the endpoint name by passing *endpoint* parameter to the view class constructor::

    admin = Admin(app)
    admin.add_view(MyView(endpoint='testadmin'))

   In this case, you can generate links by concatenating the view method name with an endpoint::

    url_for('testadmin.index')

2. If you don't override the endpoint name, the lower-case class name can be used for generating URLs, like in::

    url_for('myview.index')

3. For model-based views the rules differ - the model class name should be used if an endpoint name is not provided. The ModelView also has these endpoints by default: *.index_view*, *.create_view*, and *.edit_view*. So, the following urls can be generated for a model named "User"::

    # List View
    url_for('user.index_view')

    # Create View (redirect back to index_view)
    url_for('user.create_view', url=url_for('user.index_view'))

    # Edit View for record #1 (redirect back to index_view)
    url_for('user.edit_view', id=1, url=url_for('user.index_view'))


Further Reading
==================

****

.. toctree::
   :maxdepth: 2

   advanced
   adding_a_new_model_backend
   api/index
   changelog

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
