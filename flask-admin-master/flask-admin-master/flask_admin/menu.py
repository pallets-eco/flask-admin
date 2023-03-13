from flask import url_for


class BaseMenu(object):
    """
        Base menu item
    """
    def __init__(self, name, class_name=None, icon_type=None, icon_value=None, target=None):
        self.name = name
        self.class_name = class_name if class_name is not None else ''
        self.icon_type = icon_type
        self.icon_value = icon_value
        self.target = target

        self.parent = None
        self._children = []

    def add_child(self, menu):
        # TODO: Check if menu item is already assigned to some parent
        menu.parent = self
        self._children.append(menu)

    def get_url(self):
        raise NotImplementedError()

    def is_category(self):
        return False

    def is_active(self, view):
        for c in self._children:
            if c.is_active(view):
                return True

        return False

    def get_class_name(self):
        return self.class_name

    def get_icon_type(self):
        return self.icon_type

    def get_icon_value(self):
        return self.icon_value

    def is_visible(self):
        return True

    def is_accessible(self):
        return True

    def get_children(self):
        return [c for c in self._children if c.is_accessible() and c.is_visible()]


class MenuCategory(BaseMenu):
    """
        Menu category item.
    """
    def get_url(self):
        return None

    def is_category(self):
        return True

    def is_visible(self):
        for c in self._children:
            if c.is_visible():
                return True

        return False

    def is_accessible(self):
        for c in self._children:
            if c.is_accessible():
                return True

        return False


class MenuView(BaseMenu):
    """
        Admin view menu item
    """
    def __init__(self, name, view=None, cache=True):
        super(MenuView, self).__init__(name,
                                       class_name=view.menu_class_name,
                                       icon_type=view.menu_icon_type,
                                       icon_value=view.menu_icon_value)

        self._view = view
        self._cache = cache
        self._cached_url = None

        view.menu = self

    def get_url(self):
        if self._view is None:
            return None

        if self._cached_url:
            return self._cached_url

        url = self._view.get_url('%s.%s' % (self._view.endpoint, self._view._default_view))

        if self._cache:
            self._cached_url = url

        return url

    def is_active(self, view):
        if view == self._view:
            return True

        return super(MenuView, self).is_active(view)

    def is_visible(self):
        if self._view is None:
            return False

        return self._view.is_visible()

    def is_accessible(self):
        if self._view is None:
            return False

        return self._view.is_accessible()


class MenuLink(BaseMenu):
    """
        Link item
    """
    def __init__(self, name, url=None, endpoint=None, category=None, class_name=None,
                 icon_type=None, icon_value=None, target=None):
        super(MenuLink, self).__init__(name, class_name, icon_type, icon_value, target)

        self.category = category

        self.url = url
        self.endpoint = endpoint

    def get_url(self):
        return self.url or url_for(self.endpoint)


class SubMenuCategory(MenuCategory):
    def __init__(self, *args, **kwargs):
        super(SubMenuCategory, self).__init__(*args, **kwargs)
        self.class_name += ' dropdown-submenu dropright'
