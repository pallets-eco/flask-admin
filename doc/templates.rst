Working with templates
======================

Flask-Admin is built on top of standard Flask template management functionality.

If you're not familiar with Jinja2 templates, take a look `here <http://jinja.pocoo.org/docs/templates/>`_. Short summary:

1. You can derive from template
2. You can override template block(s)
3. When you override template block, you can render or not render parent block if you want to


Flask Core
----------

All Flask-Admin templates should derive from `admin/master.html`.

`admin/master.html` contains following blocks:

============= ========================================================================
head_meta     Page metadata in the header
head_css      Various CSS includes in the header
head          Empty block in HTML head, in case you want to put something there
page_body     Page layout
brand         Logo in the menu bar
body          Content (that's where your view will be displayed)
tail          Empty area below content
============= ========================================================================

`admin/index.html` will be used display default `Home` admin page. By default it is empty.

Models
------

There are 3 main templates that are used to display models:

`admin/model/list.html` is list view template and contains following blocks:

================= ============================================
list_header       Table header row
list_row          Row block
list_row_actions  Row action cell with edit/remove/etc buttons
================= ============================================

`admin/model/create.html` and `admin/model/edit.html` are used to display model creation editing forms respectively. They don't contain any custom
blocks and if you want to change something, you can do it using any of the blocks found in `admin/master.html`.

Customizing templates
---------------------

You can override any used template in your Flask application by creating template with same name and relative path in your main `templates` directory.

For example, if you want to override `admin/master.html`, create `admin/templates/admin/master.html` in your application and it will be used instead of
original `admin/master.html` found in Flask-Admin package.

If you don't want to replace template completely, you can create new template, derive it from existing template, override one or more blocks and
tell Flask-Admin to use it. For model view, there is `list_template` and related properties.
