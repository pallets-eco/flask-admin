from functools import wraps
from re import sub

from flask import Blueprint, render_template, url_for, abort


def expose(url='/', methods=('GET',)):
    """
        Use this decorator to expose views in your view classes.

        `url`
            Relative URL for the view
        `methods`
            Allowed HTTP methods. By default only GET is allowed.
    """
    def wrap(f):
        if not hasattr(f, '_urls'):
            f._urls = []
        f._urls.append((url, methods))
        return f

    return wrap


# Base views
def _wrap_view(f):
    @wraps(f)
    def inner(self, **kwargs):
        h = self._handle_view(f.__name__, **kwargs)

        if h is not None:
            return h

        return f(self, **kwargs)

    return inner


class AdminViewMeta(type):
    """
        View metaclass.

        Does some precalculations (like getting list of view methods from the class) to avoid
        calculating them for each view class instance.
    """
    def __init__(cls, classname, bases, fields):
        type.__init__(cls, classname, bases, fields)

        # Gather exposed views
        cls._urls = []
        cls._default_view = None

        for p in dir(cls):
            attr = getattr(cls, p)

            if hasattr(attr, '_urls'):
                # Collect methods
                for url, methods in attr._urls:
                    cls._urls.append((url, p, methods))

                    if url == '/':
                        cls._default_view = p

                # Wrap views
                setattr(cls, p, _wrap_view(attr))

        # Default view
        if cls._default_view is None and cls._urls:
            raise Exception('Missing default view for the admin view %s' % classname)


class BaseView(object):
    """
        Base administrative view.

        Derive from this class to implement your administrative interface piece. For example::

            class MyView(BaseView):
                @expose('/')
                def index(self):
                    return 'Hello World!'
    """
    __metaclass__ = AdminViewMeta

    def __init__(self, name=None, category=None, endpoint=None, url=None, static_folder=None):
        """
            Constructor.

            `name`
                Name of this view. If not provided, will be defaulted to the class name.
            `category`
                View category. If not provided, will be shown as a top-level menu item. Otherwise, will
                be in a submenu.
            `endpoint`
                Base endpoint name for the view. For example, if there's view method called "index" and
                endpoint was set to "myadmin", you can use `url_for('myadmin.index')` to get URL to the
                view method. By default, equals to the class name in lower case.
            `url`
                Base URL. If provided, affects how URLs are generated. For example, if url parameter
                equals to "test", resulting URL will look like "/admin/test/". If not provided, will
                use endpoint as a base url. However, if URL starts with '/', absolute path is assumed
                and '/admin/' prefix won't be applied.
        """
        self.name = name
        self.category = category
        self.endpoint = endpoint
        self.url = url
        self.static_folder = static_folder

        # Initialized from create_blueprint
        self.admin = None
        self.blueprint = None

    def create_blueprint(self, admin):
        """
            Create Flask blueprint.
        """
        # Store admin instance
        self.admin = admin

        # If endpoint name is not provided, get it from the class name
        if self.endpoint is None:
            self.endpoint = self.__class__.__name__.lower()

        # If url is not provided, generate it from endpoint name
        if self.url is None:
            self.url = '%s/%s' % (self.admin.url, self.endpoint)
        else:
            if not self.url.startswith('/'):
                self.url = '%s/%s' % (self.admin.url, self.url)

        # If name is not povided, use capitalized endpoint name
        if self.name is None:
            self.name = self._prettify_name(self.__class__.__name__)

        # Create blueprint and register rules
        self.blueprint = Blueprint(self.endpoint, __name__,
                                   url_prefix=self.url,
                                   template_folder='templates',
                                   static_folder=self.static_folder)

        for url, name, methods in self._urls:
            self.blueprint.add_url_rule(url,
                                        name,
                                        getattr(self, name),
                                        methods=methods)

        return self.blueprint

    def render(self, template, **kwargs):
        """
            Render template

            `template`
                Template path to render
            `kwargs`
                Template arguments
        """
        # Store
        kwargs['admin_view'] = self

        return render_template(template, **kwargs)

    def _prettify_name(self, name):
        """
            Prettify class name by splitting name by capital characters. So, 'MySuperClass' will look like 'My Super Class'

            `name`
                String to prettify
        """
        return sub(r'(?<=.)([A-Z])', r' \1', name)

    def is_accessible(self):
        """
            Override this method to add permission checks.

            Flask-AdminEx does not make any assumptions about authentication system used in your application, so it is
            up for you to implement it.

            By default, it will allow access for the everyone.
        """
        return True

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return abort(403)


class AdminIndexView(BaseView):
    """
        Administrative interface entry page. You can see it by going to the /admin/ URL.

        You can override this page by passing your own view class to the `Admin` constructor::

            class MyHomeView(AdminIndexView):
                @expose('/')
                def index(self):
                    return render_template('adminhome.html')

            admin = Admin(index_view=MyHomeView)

        By default, has following rules:
        1. If name is not provided, will use 'Home'
        2. If endpoint is not provided, will use 'admin'
        3. If url is not provided, will use '/admin'
        4. Automatically associates with static folder.
    """
    def __init__(self, name=None, category=None, endpoint=None, url=None):
        super(AdminIndexView, self).__init__(name or 'Home', category, endpoint or 'admin', url or '/admin', 'static')

    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class MenuItem(object):
    """
        Simple menu tree hierarchy.
    """
    def __init__(self, name, view=None):
        self.name = name
        self._view = view
        self._children = []
        self._children_urls = set()

        self.url = None
        if view is not None:
            self.url = view.url

    def add_child(self, view):
        self._children.append(view)
        self._children_urls.add(view.url)

    def get_url(self):
        if self._view is None:
            return None

        # TODO: Optimize me
        return url_for('%s.%s' % (self._view.endpoint, self._view._default_view))

    def is_active(self, view):
        if view == self._view:
            return True

        return view.url in self._children_urls

    def is_accessible(self):
        if self._view is None:
            return False

        return self._view.is_accessible()

    def is_category(self):
        return self._view is None

    def get_children(self):
        return [c for c in self._children if c.is_accessible()]

    def __repr__(self):
        return 'MenuItem %s (%s)' % (self.name, repr(self._children))


class Admin(object):
    """
        Collection of the views. Also manages menu structure.
    """
    def __init__(self, name=None, url=None, index_view=None):
        """
            Constructor.

            `name`
                Application name. Will be displayed in main menu and as a page title. If not provided, defaulted to "Admin"
            `index_view`
                Home page view to use. If not provided, will use `AdminIndexView`.
        """
        self._views = []
        self._menu = []

        if name is None:
            name = 'Admin'
        self.name = name

        if url is None:
            url = '/admin'
        self.url = url

        if index_view is None:
            index_view = AdminIndexView()

        # Add predefined index view
        self.add_view(index_view)

    def add_view(self, view):
        """
            Add view to the collection.

            `view`
                View to add.
        """
        self._views.append(view)

    def setup_app(self, app):
        """
            Register all views with Flask application.

            `app`
                Flask application instance
        """
        self.app = app

        for v in self._views:
            app.register_blueprint(v.create_blueprint(self))

        self._refresh_menu()

    def _refresh_menu(self):
        categories = dict()

        self._menu = []

        for v in self._views:
            if v.category is None:
                self._menu.append(MenuItem(v.name, v))
            else:
                category = categories.get(v.category)

                if category is None:
                    category = MenuItem(v.category)
                    categories[v.category] = category
                    self._menu.append(category)

                category.add_child(MenuItem(v.name, v))

    def menu(self):
        """
            Return menu hierarchy.
        """
        return self._menu
