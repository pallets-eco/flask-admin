from functools import wraps

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

    def __init__(self, name=None, endpoint=None, url=None, static_folder=None):
        self.name = name
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
            self.name = self.endpoint.capitalize()

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

    def is_accessible(self):
        return True

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return abort(403)


class AdminIndexView(BaseView):
    def __init__(self, name=None, endpoint=None, url=None):
        super(AdminIndexView, self).__init__(name or 'Home', endpoint or 'admin', url or '/admin/', 'static')

    @expose('/')
    def index(self):
        return render_template('admin/index.html', view=self)


class Admin(object):
    def __init__(self, app, index_view=None):
        self.app = app
        self._views = []

        if index_view is None:
            index_view = AdminIndexView()

        # Add predefined index view
        self.add_view(index_view)

    def add_view(self, view):
        # Store in list of views and associate view with admin instance
        self._views.append(view)
        view._set_admin(self)

        # Register blueprint
        self.app.register_blueprint(view.blueprint)

    @property
    def menu(self):
        # TODO: Precalculate URL - no need to get URLs for every request
        return (('%s.%s' % (v.endpoint, v._default_view), v.url, v.name) for v in self._views if v.is_accessible())
