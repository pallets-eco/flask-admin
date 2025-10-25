import os.path as op
import typing as t
import warnings
from functools import wraps

from flask import abort
from flask import current_app
from flask import Flask
from flask import g
from flask import render_template
from flask import url_for
from flask.views import MethodView
from flask.views import View
from markupsafe import Markup

from flask_admin import babel
from flask_admin import helpers as h
from flask_admin._compat import as_unicode

# For compatibility reasons import MenuLink
from flask_admin.blueprints import _BlueprintWithHostSupport as Blueprint
from flask_admin.consts import ADMIN_ROUTES_HOST_VARIABLE
from flask_admin.menu import BaseMenu  # noqa: F401
from flask_admin.menu import MenuCategory  # noqa: F401
from flask_admin.menu import MenuLink  # noqa: F401
from flask_admin.menu import MenuView  # noqa: F401
from flask_admin.menu import SubMenuCategory  # noqa: F401
from flask_admin.theme import Bootstrap4Theme
from flask_admin.theme import Theme


def expose(url: str = "/", methods: t.Iterable[str] | None = ("GET",)) -> t.Callable:
    """
    Use this decorator to expose views in your view classes.

    :param url:
        Relative URL for the view
    :param methods:
        Allowed HTTP methods. By default only GET is allowed.
    """

    def wrap(f: AdminViewMeta) -> AdminViewMeta:
        if not hasattr(f, "_urls"):
            f._urls = []
        f._urls.append((url, methods))  # type: ignore[arg-type]
        return f

    return wrap


def expose_plugview(url: str = "/") -> t.Callable:
    """
    Decorator to expose Flask's pluggable view classes
    (``flask.views.View`` or ``flask.views.MethodView``).

    :param url:
        Relative URL for the view

    .. versionadded:: 1.0.4
    """

    def wrap(v: View | MethodView) -> t.Any:
        handler = expose(url, v.methods)

        if hasattr(v, "as_view"):
            return handler(v.as_view(v.__name__))  # type:ignore[union-attr]
        else:
            return handler(v)

    return wrap


# Base views
def _wrap_view(f: t.Callable) -> t.Callable:
    # Avoid wrapping view method twice
    if hasattr(f, "_wrapped"):
        return f

    @wraps(f)
    def inner(self: t.Any, *args: t.Any, **kwargs: t.Any) -> t.Any:
        # Store current admin view
        h.set_current_view(self)

        # Check if administrative piece is accessible
        abort = self._handle_view(f.__name__, **kwargs)
        if abort is not None:
            return abort

        return self._run_view(current_app.ensure_sync(f), *args, **kwargs)

    inner._wrapped = True  # type:ignore[attr-defined]

    return inner


class AdminViewMeta(type):
    """
    View metaclass.

    Does some precalculations (like getting list of view methods from the class) to
    avoid calculating them for each view class instance.
    """

    def __init__(
        cls, classname: str, bases: tuple[type, ...], fields: dict[str, t.Any]
    ) -> None:
        type.__init__(cls, classname, bases, fields)

        # Gather exposed views
        cls._urls: list[
            tuple[str, t.Iterable[str]] | tuple[str, str, t.Iterable[str]]
        ] = []
        cls._default_view = None

        for p in dir(cls):
            attr = getattr(cls, p)

            if hasattr(attr, "_urls"):
                # Collect methods
                for url, methods in attr._urls:
                    cls._urls.append((url, p, methods))

                    if url == "/":
                        cls._default_view = p

                # Wrap views
                setattr(cls, p, _wrap_view(attr))


class BaseViewClass:
    pass


class BaseView(BaseViewClass, metaclass=AdminViewMeta):
    """
    Base administrative view.

    Derive from this class to implement your administrative interface piece. For
    example::

        from flask_admin import BaseView, expose
        class MyView(BaseView):
            @expose('/')
            def index(self):
                return 'Hello World!'

    Icons can be added to the menu by using `menu_icon_type` and `menu_icon_value`. For
    example::

        admin.add_view(
            MyView(
                name='My View', menu_icon_type='bi', menu_icon_value='bi-house'
            )
        )
    """

    extra_css: list[str] = []
    """Extra CSS files to include in the page"""

    extra_js: list[str] = []
    """Extra JavaScript files to include in the page"""

    @property
    def _template_args(self) -> dict:
        """
        Extra template arguments.

        If you need to pass some extra parameters to the template,
        you can override particular view function, contribute
        arguments you want to pass to the template and call parent view.

        These arguments are local for this request and will be discarded
        in the next request.

        Any value passed through ``_template_args`` will override whatever
        parent view function passed to the template.

        For example::

            class MyAdmin(ModelView):
                @expose('/')
                def index(self):
                    self._template_args['name'] = 'foobar'
                    self._template_args['code'] = '12345'
                    super(MyAdmin, self).index()
        """
        args = getattr(g, "_admin_template_args", None)

        if args is None:
            args = g._admin_template_args = dict()

        return args

    def __init__(
        self,
        name: str | None = None,
        category: str | None = None,
        endpoint: str | None = None,
        url: str | None = None,
        static_folder: str | None = None,
        static_url_path: str | None = None,
        menu_class_name: str | None = None,
        menu_icon_type: str | None = None,
        menu_icon_value: str | None = None,
    ) -> None:
        """
        Constructor.

        :param name:
            Name of this view. If not provided, will default to the class name.
        :param category:
            View category. If not provided, this view will be shown as a top-level menu
            item. Otherwise, it will be in a submenu.
        :param endpoint:
            Base endpoint name for the view. For example, if there's a view method
            called "index" and endpoint is set to "myadmin", you can use
            `url_for('myadmin.index')` to get the URL to the view method. Defaults to
            the class name in lower case.
        :param url:
            Base URL. If provided, affects how URLs are generated. For example, if the
            url parameter is "test", the resulting URL will look like "/admin/test/".
            If not provided, will use endpoint as a base url. However, if URL starts
            with '/', absolute path is assumed and '/admin/' prefix won't be applied.
        :param static_url_path:
            Static URL Path. If provided, this specifies the path to the static url
            directory.
        :param menu_class_name:
            Optional class name for the menu item.
        :param menu_icon_type:
            Optional icon. Possible icon types:

             - `flask_admin.consts.ICON_TYPE_BOOTSTRAP` - Bootstrap icon
             - `flask_admin.consts.ICON_TYPE_FONT_AWESOME` - Font Awesome icon
             - `flask_admin.consts.ICON_TYPE_IMAGE` - Image relative to Flask static
                directory
             - `flask_admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
        :param menu_icon_value:
            Icon name (fontawesome, or bootstrap) or URL, depending on
            `menu_icon_type` setting
        """
        self.name = name
        self.category = category
        self.endpoint = self._get_endpoint(endpoint)
        self.url = url
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.menu: MenuView | None = None

        self.menu_class_name = menu_class_name
        self.menu_icon_type = menu_icon_type
        self.menu_icon_value = menu_icon_value

        # Initialized from create_blueprint
        self.admin: Admin | None = None
        self.blueprint: Blueprint | None = None

        # Default view
        if self._default_view is None:  # type: ignore[attr-defined]
            raise Exception(
                f"Attempted to instantiate admin view {self.__class__.__name__} "
                "without default view"
            )

    def _get_endpoint(self, endpoint: str | None) -> str:
        """
        Generate Flask endpoint name. By default converts class name to lower case if
        endpoint is not explicitly provided.
        """
        if endpoint:
            return endpoint

        return self.__class__.__name__.lower()

    def _get_view_url(self, admin: "Admin", url: str | None) -> str:
        """
        Generate URL for the view. Override to change default behavior.
        """
        if url is None:
            if admin.url != "/":
                url = f"{admin.url}/{self.endpoint}"
            else:
                if self == admin.index_view:
                    url = "/"
                else:
                    url = f"/{self.endpoint}"
        else:
            if not url.startswith("/"):
                url = f"{admin.url}/{url}"

        return url

    def create_blueprint(self, admin: "Admin") -> Blueprint:
        """
        Create Flask blueprint.
        """
        # Store admin instance
        self.admin = admin

        # If the static_url_path is not provided, use the admin's
        if not self.static_url_path:
            self.static_url_path = admin.static_url_path

        # Generate URL
        self.url = self._get_view_url(admin, self.url)

        # If we're working from the root of the site, set prefix to None
        if self.url == "/":
            self.url = None
            # prevent admin static files from conflicting with flask static files
            if not self.static_url_path:
                self.static_folder = "static"
                self.static_url_path = "/static/admin"

        # If name is not provided, use capitalized endpoint name
        if self.name is None:
            self.name = self._prettify_class_name(self.__class__.__name__)

        # Create blueprint and register rules
        self.blueprint = Blueprint(
            self.endpoint,
            __name__,
            url_prefix=self.url,
            subdomain=self.admin.subdomain,
            template_folder=op.join("templates", self.admin.theme.folder),
            static_folder=self.static_folder,
            static_url_path=self.static_url_path,
        )
        self.blueprint.attach_url_defaults_and_value_preprocessor(
            app=self.admin.app,  # type:ignore[arg-type]
            host=self.admin.host,  # type: ignore[arg-type]
        )

        for url, name, methods in self._urls:  # type: ignore[attr-defined]
            self.blueprint.add_url_rule(url, name, getattr(self, name), methods=methods)

        return self.blueprint

    def render(self, template: str, **kwargs: t.Any) -> str:
        """
        Render template

        :param template:
            Template path to render
        :param kwargs:
            Template arguments
        """
        # Store self as admin_view
        kwargs["admin_view"] = self
        kwargs["admin_base_template"] = self.admin.theme.base_template  # type: ignore[union-attr]
        kwargs["admin_csp_nonce_attribute"] = (
            Markup(f'nonce="{self.admin.csp_nonce_generator()}"')  # type: ignore[union-attr]
            if self.admin.csp_nonce_generator  # type: ignore[union-attr]
            else ""
        )

        # Provide i18n support even if flask-babel is not installed
        # or enabled.
        kwargs["_gettext"] = babel.gettext
        kwargs["_ngettext"] = babel.ngettext
        kwargs["h"] = h

        # Expose get_url helper
        kwargs["get_url"] = self.get_url

        # Expose config info
        kwargs["config"] = current_app.config
        kwargs["theme"] = self.admin.theme  # type: ignore[union-attr]

        # Contribute extra arguments
        kwargs.update(self._template_args)

        return render_template(template, **kwargs)

    def _prettify_class_name(self, name: str) -> str:
        """
        Split words in PascalCase string into separate words.

        :param name:
            String to prettify
        """
        return h.prettify_class_name(name)

    def is_visible(self) -> bool:
        """
        Override this method if you want dynamically hide or show administrative views
        from Flask-Admin menu structure

        By default, item is visible in menu.

        Please note that item should be both visible and accessible to be displayed in
        menu.
        """
        return True

    def is_accessible(self) -> bool:
        """
        Override this method to add permission checks.

        Flask-Admin does not make any assumptions about the authentication system used
        in your application, so it is up to you to implement it.

        By default, it will allow access for everyone.
        """
        return True

    def _handle_view(self, name: str, **kwargs: dict[str, t.Any]) -> t.Any:
        """
        This method will be executed before calling any view method.

        It will execute the ``inaccessible_callback`` if the view is not
        accessible.

        :param name:
            View function name
        :param kwargs:
            View function arguments
        """
        if not self.is_accessible():
            return self.inaccessible_callback(name, **kwargs)

    def _run_view(
        self, fn: t.Callable, *args: tuple[t.Any], **kwargs: dict[str, t.Any]
    ) -> t.Any:
        """
        This method will run actual view function.

        While it is similar to _handle_view, can be used to change
        arguments that are passed to the view.

        :param fn:
            View function
        :param kwargs:
            Arguments
        """
        try:
            return fn(self, *args, **kwargs)
        except TypeError:
            return fn(cls=self, **kwargs)

    def inaccessible_callback(self, name: t.Any, **kwargs: t.Any) -> t.Any:
        """
        Handle the response to inaccessible views.

        By default, it throw HTTP 403 error. Override this method to
        customize the behaviour.
        """
        return abort(403)

    def get_url(self, endpoint: str, **kwargs: t.Any) -> str:
        """
        Generate URL for the endpoint. If you want to customize URL generation
        logic (persist some query string argument, for example), this is
        right place to do it.

        :param endpoint:
            Flask endpoint name
        :param kwargs:
            Arguments for `url_for`
        """
        return url_for(endpoint, **kwargs)

    @property
    def _debug(self) -> bool:
        if not self.admin or not self.admin.app:
            return False

        return self.admin.app.debug


class AdminIndexView(BaseView):
    """
    Default administrative interface index page when visiting the ``/admin/`` URL.

    It can be overridden by passing your own view class to the ``Admin`` constructor::

        class MyHomeView(AdminIndexView):
            @expose('/')
            def index(self):
                arg1 = 'Hello'
                return self.render('admin/myhome.html', arg1=arg1)

        admin = Admin(index_view=MyHomeView())


    Also, you can change the root url from /admin to / with the following::

        admin = Admin(
            app,
            index_view=AdminIndexView(
                name='Home',
                template='admin/myhome.html',
                url='/'
            )
        )

    Default values for the index page are:

    * If a name is not provided, 'Home' will be used.
    * If an endpoint is not provided, will default to ``admin``
    * Default URL route is ``/admin``.
    * Automatically associates with static folder.
    * Default template is ``admin/index.html``
    """

    def __init__(
        self,
        name: str | None = None,
        category: str | None = None,
        endpoint: str | None = None,
        url: str | None = None,
        template: str = "admin/index.html",
        menu_class_name: str | None = None,
        menu_icon_type: str | None = None,
        menu_icon_value: str | None = None,
    ) -> None:
        super().__init__(
            name or babel.lazy_gettext("Home"),
            category,
            endpoint or "admin",
            "/admin" if url is None else url,
            "static",
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value,
        )
        self._template = template

    @expose()
    def index(self) -> str:
        return self.render(self._template)


class Admin:
    """
    Collection of the admin views. Also manages menu structure.
    """

    def __init__(
        self,
        app: Flask | None = None,
        name: str | None = None,
        url: str | None = None,
        subdomain: str | None = None,
        index_view: AdminIndexView | None = None,
        translations_path: str | None = None,
        endpoint: str | None = None,
        static_url_path: str | None = None,
        theme: Theme | None = None,
        category_icon_classes: dict[str, str] | None = None,
        host: str | None = None,
        csp_nonce_generator: t.Callable | None = None,
    ) -> None:
        """
        Constructor.

        :param app:
            Flask application object
        :param name:
            Application name. Will be displayed in the main menu and as a page title.
            Defaults to "Admin"
        :param url:
            Base URL
        :param subdomain:
            Subdomain to use
        :param index_view:
            Home page view to use. Defaults to `AdminIndexView`.
        :param translations_path:
            Location of the translation message catalogs. By default will use the
            translations shipped with Flask-Admin.
        :param endpoint:
            Base endpoint name for index view. If you use multiple instances of the
            `Admin` class with a single Flask application, you have to set a unique
            endpoint name for each instance.
        :param static_url_path:
            Static URL Path. If provided, this specifies the default path to the static
            url directory for all its views. Can be overridden in view configuration.
        :param theme:
            Base theme. Defaults to `Bootstrap4Theme()`.
        :param category_icon_classes:
            A dict of category names as keys and html classes as values to be added to
            menu category icons. Example: {'Favorites': 'bi bi-star-fill'}
        :param host:
            The host to register all admin views on. Mutually exclusive with `subdomain`
        :param csp_nonce_generator:
            A callable that returns a nonce to inject into Flask-Admin JS, CSS, etc.
        """
        self.app = app

        self.translations_path = translations_path

        self._views = []  # type: ignore[var-annotated]
        self._menu = []  # type: ignore[var-annotated]
        self._menu_categories: dict[str, MenuCategory] = dict()
        self._menu_links = []  # type: ignore[var-annotated]

        if name is None:
            name = "Admin"
        self.name = name

        self.index_view = index_view or AdminIndexView(endpoint=endpoint, url=url)
        self.endpoint = endpoint or self.index_view.endpoint
        self.url = url or self.index_view.url
        self.static_url_path = static_url_path
        self.subdomain = subdomain
        self.host = host
        self.theme: Theme = theme or Bootstrap4Theme()
        self.category_icon_classes = category_icon_classes or dict()

        self._validate_admin_host_and_subdomain()

        self.csp_nonce_generator = csp_nonce_generator

        # Add index view
        self._set_admin_index_view(index_view=index_view, endpoint=endpoint, url=url)

        # Register with application
        if app is not None:
            self._init_extension()

    def _validate_admin_host_and_subdomain(self) -> None:
        if self.subdomain is not None and self.host is not None:
            raise ValueError("`subdomain` and `host` are mutually-exclusive")

        if self.host is None:
            return

        if self.app and not self.app.url_map.host_matching:
            raise ValueError(
                "`host` should only be set if your Flask app is using `host_matching`."
            )

        if self.host.strip() in {"*", ADMIN_ROUTES_HOST_VARIABLE}:
            self.host = ADMIN_ROUTES_HOST_VARIABLE

        elif "<" in self.host and ">" in self.host:
            raise ValueError(
                "`host` must either be a host name with no variables, to serve all "
                "Flask-Admin routes from a single host, or `*` to match the current "
                "request's host."
            )

    def add_view(self, view: BaseView) -> None:
        """
        Add a view to the collection.

        :param view:
            View to add.
        """
        # Add to views
        self._views.append(view)

        # If app was provided in constructor, register view with Flask app
        if self.app is not None:
            self.app.register_blueprint(
                view.create_blueprint(self),
                host=self.host,
            )

        self._add_view_to_menu(view)

    def _set_admin_index_view(
        self,
        index_view: AdminIndexView | None = None,
        endpoint: str | None = None,
        url: str | None = None,
    ) -> None:
        """
          Add the admin index view.

        :param index_view:
             Home page view to use. Defaults to `AdminIndexView`.
         :param url:
             Base URL
        :param endpoint:
             Base endpoint name for index view. If you use multiple instances of the
             `Admin` class with a single Flask application, you have to set a unique
             endpoint name for each instance.
        """
        self.index_view: AdminIndexView = (  # type: ignore[no-redef]
            index_view or AdminIndexView(endpoint=endpoint, url=url)
        )
        self.endpoint = endpoint or self.index_view.endpoint
        self.url = url or self.index_view.url

        # Add predefined index view
        # assume index view is always the first element of views.
        if len(self._views) > 0:
            self._views[0] = self.index_view
            self._menu[0] = MenuView(
                self.index_view.name,  # type: ignore[arg-type]
                self.index_view,
            )
        else:
            self.add_view(self.index_view)

    def add_views(self, *args: t.Any) -> None:
        """
        Add one or more views to the collection.

        Examples::

            admin.add_views(view1)
            admin.add_views(view1, view2, view3, view4)
            admin.add_views(*my_list)

        :param args:
            Argument list including the views to add.
        """
        for view in args:
            self.add_view(view)

    def add_category(
        self,
        name: str,
        class_name: str | None = None,
        icon_type: str | None = None,
        icon_value: str | None = None,
    ) -> None:
        """
        Add a category of a given name

        :param name:
            The name of the new menu category.
        :param class_name:
            The class name for the new menu category.
        :param icon_type:
            The icon name for the new menu category.
        :param icon_value:
            The icon value for the new menu category.
        """
        cat_text = as_unicode(name)

        category = self.get_category_menu_item(name)
        if category:
            return

        category = MenuCategory(
            name, class_name=class_name, icon_type=icon_type, icon_value=icon_value
        )
        self._menu_categories[cat_text] = category
        self._menu.append(category)

    def add_sub_category(self, name: str, parent_name: str) -> None:
        """
        Add a category of a given name underneath
        the category with parent_name.

        :param name:
            The name of the new menu category.
        :param parent_name:
            The name of a parent_name category
        """

        name_text = as_unicode(name)
        parent_name_text = as_unicode(parent_name)
        category = self.get_category_menu_item(name_text)
        parent = self.get_category_menu_item(parent_name_text)
        if category is None and parent is not None:
            category = SubMenuCategory(name)
            self._menu_categories[name_text] = category
            parent.add_child(category)

    def add_link(self, link: MenuLink) -> None:
        """
        Add link to menu links collection.

        :param link:
            Link to add.
        """
        if link.category:
            self.add_menu_item(link, link.category)
        else:
            self._menu_links.append(link)

    def add_links(self, *args: MenuLink) -> None:
        """
        Add one or more links to the menu links collection.

        Examples::

            admin.add_links(link1)
            admin.add_links(link1, link2, link3, link4)
            admin.add_links(*my_list)

        :param args:
            Argument list including the links to add.
        """
        for link in args:
            self.add_link(link)

    def add_menu_item(
        self, menu_item: BaseMenu, target_category: str | None = None
    ) -> None:
        """
        Add menu item to menu tree hierarchy.

        :param menu_item:
            MenuItem class instance
        :param target_category:
            Target category name
        """
        if target_category:
            cat_text = as_unicode(target_category)

            category = self._menu_categories.get(cat_text)

            # create a new menu category if one does not exist already
            if category is None:
                category = MenuCategory(target_category)
                category.class_name = self.category_icon_classes.get(
                    cat_text
                    # type:ignore[assignment]
                )
                self._menu_categories[cat_text] = category

                self._menu.append(category)

            category.add_child(menu_item)
        else:
            self._menu.append(menu_item)

    def _add_menu_item(
        self, menu_item: BaseMenu, target_category: str | None = None
    ) -> None:
        warnings.warn(
            "Admin._add_menu_item is obsolete - use Admin.add_menu_item instead.",
            stacklevel=1,
        )
        return self.add_menu_item(menu_item, target_category)

    def _add_view_to_menu(self, view: BaseView) -> None:
        """
        Add a view to the menu tree

        :param view:
            View to add
        """
        self.add_menu_item(
            MenuView(
                view.name,  # type: ignore[arg-type]
                view,
            ),
            view.category,
        )

    def get_category_menu_item(self, name: str) -> MenuCategory | None:
        return self._menu_categories.get(name)

    def init_app(
        self,
        app: Flask,
        index_view: AdminIndexView | None = None,
        endpoint: str | None = None,
        url: str | None = None,
    ) -> None:
        """
        Register all views with the Flask application.
        """
        self.app = app
        self._validate_admin_host_and_subdomain()

        self._init_extension()

        # Register Index view
        if index_view is not None:
            self._set_admin_index_view(
                index_view=index_view, endpoint=endpoint, url=url
            )

        # Register views
        for view in self._views:
            app.register_blueprint(view.create_blueprint(self), host=self.host)

    def _init_extension(self) -> None:
        if not hasattr(self.app, "extensions"):
            self.app.extensions = dict()  # type: ignore[attr-defined]

        admins = self.app.extensions.get("admin", [])  # type: ignore[union-attr]

        for p in admins:
            if p.endpoint == self.endpoint:
                raise Exception(
                    "Cannot have two Admin() instances with same" " endpoint name."
                )

            if p.url == self.url and p.subdomain == self.subdomain:
                raise Exception(
                    "Cannot assign two Admin() instances with same"
                    " URL and subdomain to the same application."
                )

        admins.append(self)
        self.app.extensions["admin"] = admins  # type: ignore[union-attr]

    def menu(self) -> list:
        """
        Return the menu hierarchy.
        """
        return self._menu

    def menu_links(self) -> list:
        """
        Return menu links.
        """
        return self._menu_links
