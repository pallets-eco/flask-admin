Adding your own views
======================
For situations where your requirements are really specific, and you struggle to meet
them with the builtin :class:`~flask_admin.model.ModelView` class: Flask-Admin makes it really easy for you to
take full control and ass some views yourself.

Standalone views
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
it is served at the root URL, '/'. This is a restriction on standalone views: each view class needs
to serve a view at its root.

The `analytics_index.html` template for the example above, could look something like::

    {% extends 'admin/master.html' %}
    {% block body %}
        <p>Here I'm going to display some data.</p>
    {% endblock %}

By extending the *admin/master.html* template, you can maintain a consistent user experience,
even while having tight control over your page's content.

Overriding the builtin views
------------------------------------

If you want most of the builtin ModelView functionality, but you want to have your own view
in place of the default `create`, `edit`, or `list` view. Then you can simply override
override the view in question::

    from flask_admin.contrib.sqla import ModelView

    # Flask and Flask-SQLAlchemy initialization here

    class UserView(ModelView):
    @expose('/new/', methods=('GET', 'POST'))
        def create_view(self):
        """
            Custom create view.
        """

        return self.render('create_user.html')

