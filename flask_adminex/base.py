from functools import wraps
from re import sub

from flask import Blueprint, render_template, url_for, abort


def expose(url='/', methods=('GET',)):
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
    __metaclass__ = AdminViewMeta

    def __init__(self, name=None, category=None, endpoint=None, url=None, static_folder=None):
        self.name = name
        self.category = category
        self.endpoint = endpoint
        self.url = url
        self.static_folder = static_folder

        self.admin = None

        self._create_blueprint()

    def _set_admin(self, admin):
        self.admin = admin

    def _create_blueprint(self):
        # If endpoint name is not provided, get it from the class name
        if self.endpoint is None:
            self.endpoint = self.__class__.__name__.lower()

        # If url is not provided, generate it from endpoint name
        if self.url is None:
            self.url = '/admin/%s' % self.endpoint

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

    def _prettify_name(self, name):
        return sub(r'(?<=.)([A-Z])', r' \1', name)

    def is_accessible(self):
        return True

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return abort(403)


class AdminIndexView(BaseView):
    def __init__(self, name=None, category=None, endpoint=None, url=None):
        super(AdminIndexView, self).__init__(name or 'Home', category, endpoint or 'admin', url or '/admin', 'static')

    @expose('/')
    def index(self):
        return render_template('admin/index.html', view=self)


class Admin(object):
    class MenuItem(object):
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

    def __init__(self, index_view=None):
        self._views = []
        self._menu = []

        if index_view is None:
            index_view = AdminIndexView()

        # Add predefined index view
        self.add_view(index_view)

    def add_view(self, view):
        view._set_admin(self)
        self._views.append(view)

    def apply(self, app):
        self.app = app

        for v in self._views:
            app.register_blueprint(v.blueprint)

        self._refresh_menu()

    def _refresh_menu(self):
        categories = dict()

        self._menu = []

        for v in self._views:
            if v.category is None:
                self._menu.append(self.MenuItem(v.name, v))
            else:
                category = categories.get(v.category)

                if category is None:
                    category = self.MenuItem(v.category)
                    categories[v.category] = category
                    self._menu.append(category)

                category.add_child(self.MenuItem(v.name, v))

        print repr(self._menu)

    def menu(self):
        return self._menu

