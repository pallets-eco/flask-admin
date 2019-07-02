:tocdepth: 2

Introduction To Flask-Admin
###########################

Getting Started
===============

****

Initialization
--------------

The first step is to initialize an empty admin interface for your Flask app::

    from flask import Flask
    from flask_admin import Admin

    app = Flask(__name__)

    # set optional bootswatch theme
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

    admin = Admin(app, name='microblog', template_mode='bootstrap3')
    # Add administrative views here

    app.run()

Here, both the *name* and *template_mode* parameters are optional. Alternatively,
you could use the :meth:`~flask_admin.base.Admin.init_app` method.

If you start this application and navigate to `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_,
you should see an empty page with a navigation bar on top. Customize the look by
specifying a Bootswatch theme that suits your needs (see http://bootswatch.com/3/ for available swatches).

Adding Model Views
------------------

Model views allow you to add a dedicated set of admin pages for managing any model in your database. Do this by creating
instances of the *ModelView* class, which you can import from one of Flask-Admin's built-in ORM backends. An example
is the SQLAlchemy backend, which you can use as follows::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    admin = Admin(app, name='microblog', template_mode='bootstrap3')
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Post, db.session))

Straight out of the box, this gives you a set of fully featured *CRUD* views for your model:

    * A `list` view, with support for searching, sorting, filtering, and deleting records.
    * A `create` view for adding new records.
    * An `edit` view for updating existing records.
    * An optional, read-only `details` view.

There are many options available for customizing the display and functionality of these built-in views.
For more details on that, see :ref:`customizing-builtin-views`. For more details on the other
ORM backends that are available, see :ref:`database-backends`.

Adding Content to the Index Page
--------------------------------
The first thing you'll notice when you visit `http://localhost:5000/admin/ <http://localhost:5000/admin/>`_
is that it's just an empty page with a navigation menu. To add some content to this page, save the following text as `admin/index.html` in your project's `templates` directory::

    {% extends 'admin/master.html' %}

    {% block body %}
      <p>Hello world</p>
    {% endblock %}

This will override the default index template, but still give you the built-in navigation menu.
So, now you can add any content to the index page, while maintaining a consistent user experience.

Authorization & Permissions
===========================

****

When setting up an admin interface for your application, one of the first problems
you'll want to solve is how to keep unwanted users out. With Flask-Admin there
are a few different ways of approaching this.

HTTP Basic Auth
---------------
Unfortunately, there is no easy way of applying HTTP Basic Auth just to your admin
interface.

The simplest form of authentication is HTTP Basic Auth. It doesn't interfere
with your database models, and it doesn't require you to write any new view logic or
template code. So it's great for when you're deploying something that's still
under development, before you want the whole world to see it.

Have a look at `Flask-BasicAuth <https://flask-basicauth.readthedocs.io/>`_ to see just how
easy it is to put your whole application behind HTTP Basic Auth.

Rolling Your Own
----------------
For a more flexible solution, Flask-Admin lets you define access control rules
on each of your admin view classes by simply overriding the `is_accessible` method.
How you implement the logic is up to you, but if you were to use a low-level library like
`Flask-Login <https://flask-login.readthedocs.io/>`_, then restricting access
could be as simple as::

    class MicroBlogModelView(sqla.ModelView):

        def is_accessible(self):
            return login.current_user.is_authenticated

        def inaccessible_callback(self, name, **kwargs):
            # redirect to login page if user doesn't have access
            return redirect(url_for('login', next=request.url))

In the navigation menu, components that are not accessible to a particular user will not be displayed
for that user. For an example of using Flask-Login with Flask-Admin, have a look
at https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth-flask-login.

The main drawback is that you still need to implement all of the relevant login,
registration, and account management views yourself.


Using Flask-Security
--------------------

If you want a more polished solution, you could
use `Flask-Security <https://pythonhosted.org/Flask-Security/>`_,
which is a higher-level library. It comes with lots of built-in views for doing
common things like user registration, login, email address confirmation, password resets, etc.

The only complicated bit is making the built-in Flask-Security views integrate smoothly with the
Flask-Admin templates to create a consistent user experience. To
do this, you will need to override the built-in Flask-Security templates and have them
extend the Flask-Admin base template by adding the following to the top
of each file::

    {% extends 'admin/master.html' %}

Now, you'll need to manually pass in some context variables for the Flask-Admin
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

The example only uses the built-in `register` and `login` views, but you could follow the same
approach for including the other views, like `forgot_password`, `send_confirmation`, etc.

.. _customizing-builtin-views:

Customizing Built-in Views
=========================

****

When inheriting from `ModelView`, values can be specified for numerous
configuration parameters. Use these to customize the views to suit your
particular models::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class MicroBlogModelView(ModelView):
        can_delete = False  # disable model deletion
        page_size = 50  # the number of entries to display on the list view

    admin.add_view(MicroBlogModelView(User, db.session))
    admin.add_view(MicroBlogModelView(Post, db.session))

Or, in much the same way, you can specify options for a single model at a time::

    class UserView(ModelView):
            can_delete = False  # disable model deletion

    class PostView(ModelView):
            page_size = 50  # the number of entries to display on the list view

    admin.add_view(UserView(User, db.session))
    admin.add_view(PostView(Post, db.session))


`ModelView` Configuration Attributes
------------------------------------

For a complete list of the attributes that are defined, have a look at the
API documentation for :meth:`~flask_admin.model.BaseModelView`. Here are
some of the most commonly used attributes:

To **disable some of the CRUD operations**, set any of these boolean parameters::

    can_create = False
    can_edit = False
    can_delete = False

If your model has too much data to display in the list view, you can **add a read-only
details view** by setting::

    can_view_details = True

**Removing columns** from the list view is easy, just pass a list of column names for
the *column_excludes_list* parameter::

    column_exclude_list = ['password', ]

To **make columns searchable**, or to use them for filtering, specify a list of column names::

    column_searchable_list = ['name', 'email']
    column_filters = ['country']

For a faster editing experience, enable **inline editing** in the list view::

    column_editable_list = ['name', 'last_name']

Or, have the add & edit forms display inside a **modal window** on the list page, instead of
the dedicated *create* & *edit* pages::

    create_modal = True
    edit_modal = True

You can restrict the possible values for a text-field by specifying a list of **select choices**::

    form_choices = {
        'title': [
            ('MR', 'Mr'),
            ('MRS', 'Mrs'),
            ('MS', 'Ms'),
            ('DR', 'Dr'),
            ('PROF', 'Prof.')
        ]
    }

To **remove fields** from the create and edit forms::

    form_excluded_columns = ['last_name', 'email']

To specify **WTForms field arguments**::

    form_args = {
        'name': {
            'label': 'First Name',
            'validators': [required()]
        }
    }

Or, to specify arguments to the **WTForms widgets** used to render those fields::

    form_widget_args = {
        'description': {
            'rows': 10,
            'style': 'color: black'
        }
    }

When your forms contain foreign keys, have those **related models loaded via ajax**, using::

    form_ajax_refs = {
        'user': {
            'fields': ['first_name', 'last_name', 'email'],
            'page_size': 10
        }
    }

To filter the results that are loaded via ajax, you can use::

    form_ajax_refs = {
        'active_user': QueryAjaxModelLoader('user', db.session, User,
                                     filters=["is_active=True", "id>1000"])
    }

To **manage related models inline**::

    inline_models = ['post', ]

These inline forms can be customized. Have a look at the API documentation for
:meth:`~flask_admin.contrib.sqla.ModelView.inline_models`.

To **enable csv export** of the model view::

    can_export = True

This will add a button to the model view that exports records, truncating at :attr:`~flask_admin.model.BaseModelView.export_max_rows`.


Grouping Views
==============
When adding a view, specify a value for the `category` parameter
to group related views together in the menu::

    admin.add_view(UserView(User, db.session, category="Team"))
    admin.add_view(ModelView(Role, db.session, category="Team"))
    admin.add_view(ModelView(Permission, db.session, category="Team"))

This will create a top-level menu item named 'Team', and a drop-down containing
links to the three views.

To nest related views within these drop-downs, use the `add_sub_category` method::

    admin.add_sub_category(name="Links", parent_name="Team")

And to add arbitrary hyperlinks to the menu::

  admin.add_link(MenuLink(name='Home Page', url='/', category='Links'))


Adding Your Own Views
=====================

****

For situations where your requirements are really specific and you struggle to meet
them with the built-in :class:`~flask_admin.model.ModelView` class, Flask-Admin makes it easy for you to
take full control and add your own views to the interface.

Standalone Views
----------------
A set of standalone views (not tied to any particular model) can be added by extending the
:class:`~flask_admin.base.BaseView` class and defining your own view methods. For
example, to add a page that displays some analytics data from a 3rd-party API::

    from flask_admin import BaseView, expose

    class AnalyticsView(BaseView):
        @expose('/')
        def index(self):
            return self.render('analytics_index.html')

    admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))

This will add a link to the navbar for your view. Notice that
it is served at '/', the root URL. This is a restriction on standalone views: at
the very minimum, each view class needs at least one method to serve a view at its root.

The `analytics_index.html` template for the example above, could look something like::

    {% extends 'admin/master.html' %}
    {% block body %}
      <p>Here I'm going to display some data.</p>
    {% endblock %}

By extending the *admin/master.html* template, you can maintain a consistent user experience,
even while having tight control over your page's content.

Overriding the Built-in Views
----------------------------
There may be some scenarios where you want most of the built-in ModelView
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

Working With the Built-in Templates
==================================

****

Flask-Admin uses the `Jinja2 <http://jinja.pocoo.org/docs/>`_ templating engine.

.. _extending-builtin-templates:

Extending the Built-in Templates
-------------------------------

Rather than overriding the built-in templates completely, it's best to extend them. This
will make it simpler for you to upgrade to new Flask-Admin versions in future.

Internally, the Flask-Admin templates are derived from the `admin/master.html` template.
The three most interesting templates for you to extend are probably:

* `admin/model/list.html`
* `admin/model/create.html`
* `admin/model/edit.html`

To extend the default *edit* template with your own functionality, create a template in
`templates/microblog_edit.html` to look something like::

    {% extends 'admin/model/edit.html' %}

    {% block body %}
        <h1>MicroBlog Edit View</h1>
        {{ super() }}
    {% endblock %}

Now, to make your view classes use this template, set the appropriate class property::

    class MicroBlogModelView(ModelView):
        edit_template = 'microblog_edit.html'
        # create_template = 'microblog_create.html'
        # list_template = 'microblog_list.html'
        # details_template = 'microblog_details.html'
        # edit_modal_template = 'microblog_edit_modal.html'
        # create_modal_template = 'microblog_create_modal.html'
        # details_modal_template = 'microblog_details_modal.html'

If you want to use your own base template, then pass the name of the template to
the admin constructor during initialization::

    admin = Admin(app, base_template='microblog_master.html')

Overriding the Built-in Templates
--------------------------------

To take full control over the style and layout of the admin interface, you can override
all of the built-in templates. Just keep in mind that the templates will change slightly
from one version of Flask-Admin to the next, so once you start overriding them, you
need to take care when upgrading your package version.

To override any of the built-in templates, simply copy them from
the Flask-Admin source into your project's `templates/admin/` directory.
As long as the filenames stay the same, the templates in your project directory should
automatically take precedence over the built-in ones.

Available Template Blocks
*************************

Flask-Admin defines one *base* template at `admin/master.html` that all other admin templates are derived
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

Have a look at the `layout` example at https://github.com/flask-admin/flask-admin/tree/master/examples/custom-layout
to see how you can take full stylistic control over the admin interface.

Environment Variables
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

Generating URLs
---------------

To generate the URL for a specific view, use *url_for* with a dot prefix::

    from flask import url_for

    class MyView(BaseView):
        @expose('/')
        def index(self):
            # Get URL for the test view method
            user_list_url = url_for('user.index_view')
            return self.render('index.html', user_list_url=user_list_url)

A specific record can also be referenced with::

    # Edit View for record #1 (redirect back to index_view)
    url_for('user.edit_view', id=1, url=url_for('user.index_view'))

When referencing ModelView instances, use the lowercase name of the model as the
prefix when calling *url_for*. Other views can be referenced by specifying a
unique endpoint for each, and using that as the prefix. So, you could use::

    url_for('analytics.index')

If your view endpoint was defined like::

    admin.add_view(CustomView(name='Analytics', endpoint='analytics'))
