Working with templates
======================

One great advantage of building an extension on top of Flask, is the great templating engine that
comes with the package. Jinja2 allows you to use most of the Python syntax that you are used to, inside
of your templates, helping you generate either text or code in a powerful, yet flexible way.

To explore some more of what Jinja2 can offer you, head over to their documentation at
`http://jinja.pocoo.org/docs/ <http://jinja.pocoo.org/docs/>`_. But the most important features for you to
understand in order to get started with Flask-Admin are given below.

Inheritance
-----------

Templates can extend other templates. This enables you, for example, to build the standard components of
your site into a *base* template, where they are defined only once. This template can then be extended by
other templates, where more specific content may be added.

Large applications may end up having several layers of templates, starting for example with a very general HTML
structure, and then growing more and more specific at each level, until the final layer of templates define unique
pages in the application. But it needs not be very complicated, and the majority of applications will only really
need a handful of well-designed templates.

Building blocks
---------------

With Jinja2, templates are made up of *blocks* of code, which define where a child template's contents fit into the
bigger picture, as defined by the parent template.

A parent template may define any number of these code blocks, and a child template may define content for any number
of those. So, by extending an existing template, you get to just fill-in the blanks, rather than having to deal
with lots of boilerplate code that is not really relevant to the problem at hand.

Power & Flexibility
-------------------

When a block is defined in a parent template, it can already be given some content, ensuring that something
will be rendered in that place, even if a child template chooses to ignore that block completely.

If content is defined in a child template, you have the option of also rendering the code that the parent template
may have defined in that block by calling::

 {{ super() }}

anywhere inside that block. But the default behaviour is to simply override the block entirely.

Since these template blocks are defined by name, you have a lot of freedom in how you decide to arrange / nest them
in your code.

Jinja2 & Flask Admin
--------------------

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

Adding an Index Page
--------------------

You'll notice that the 'Home' page that is created by Flask-Admin at `/admin` is largely empty. By default, the
only content on the page is a set of controls for navigating to the views that you have defined. You can change this by
creating a template at `admin/index.html` in your `templates` directory.

Working with your Models
------------------------

By default, Flask-Admin uses three pre-defined templates for displaying your models in the admin-interface:

* `admin/model/list.html`
* `admin/model/create.html`
* `admin/model/edit.html`

All three of these extend the `admin/master.html` template, and you can override them by defining your own templates,
with the same path relative to your `templates` folder.

You could also choose to extend these templates, rather than overriding them. In this case you will need to
point your classes at your own templates, rather than letting them use the defaults. For example, your own template
for the *edit* views could be defined in `templates/my_edit_template.html` to look something like::

    {% extends 'admin/model/edit.html' %}

    {% block tail %}
        {{ super() }}
        ...
    {% endblock %}

And your classes could be made to use this template by setting the appropriate class property::

    class MyModelView(ModelView):
        edit_template = 'my_edit_template.html'

The three available properties are simply called `list_template`, `create_template` and `edit_template`.


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
h                    Helpers from :mod:`~flask.ext.admin.helpers` module
==================== ================================


Customizing templates
---------------------

As noted earlier, you can override any default Flask-Admin template by creating your own template with same name and
relative path inside your own `templates` directory.

You can also override the master template, but then you need to pass your own template name to the `Admin`
constructor::

    admin = Admin(app, base_template='my_master.html')

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