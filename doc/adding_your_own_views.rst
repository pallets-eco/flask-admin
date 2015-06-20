Adding your own views
===========

Standalone views
------------
Now, lets add an administrative view. The next example will result in two items appearing in the navbar menu: *Home*
and *Hello*. To do this, you need to derive from the :class:`~flask_admin.base.BaseView` class::

    from flask import Flask
    from flask_admin import Admin, BaseView, expose

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

    app = Flask(__name__)

    admin = Admin(app)
    admin.add_view(MyView(name='Hello'))

    app.run()

One important restriction on admin views is that each view class should have a default page-view method with a root
url, '/'. The following example is correct::

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

but, this wouldn't work::

    class MyView(BaseView):
        @expose('/index/')
        def index(self):
            return self.render('index.html')

Now, create a new *index.html* file with following content::

    {% extends 'admin/master.html' %}
    {% block body %}
        Hello World from MyView!
    {% endblock %}

and place it in a *templates* directory. To maintain a consistent look and feel, all administrative pages should extend
the *admin/master.html* template.

You should now see your new admin page in action on the *Hello* page

    .. image:: images/quickstart/quickstart_2.png
        :width: 640
        :target: ../_images/quickstart_2.png

To add another level of menu items, you can specify a value for the *category* parameter when passing admin views to
the Admin instance. The category specifies the name of the top-level menu item, and all of the views that are associated
with it, will be accessible from a drop-down menu. For example::

    from flask import Flask
    from flask_admin import Admin, BaseView, expose

    class MyView(BaseView):
        @expose('/')
        def index(self):
            return self.render('index.html')

    app = Flask(__name__)

    admin = Admin(app)
    admin.add_view(MyView(name='Hello 1', endpoint='test1', category='Test'))
    admin.add_view(MyView(name='Hello 2', endpoint='test2', category='Test'))
    admin.add_view(MyView(name='Hello 3', endpoint='test3', category='Test'))
    app.run()

will look like

    .. image:: images/quickstart/quickstart_3.png
        :width: 640
        :target: ../_images/quickstart_3.png


Overriding specific model views
------------------