from flask import url_for


class BaseMenu(object):
    """
        Base menu item
    """
    def __init__(self, name):
        self.name = name
        self._children = []

    def add_child(self, menu):
        self._children.append(menu)

    def get_url(self):
        raise NotImplemented()

    def is_category(self):
        return False

    def is_active(self, view):
        for c in self._children:
            if c.is_active(view):
                return True

        return False

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
    def __init__(self, name, view=None):
        super(MenuView, self).__init__(name)

        self._view = view
        self._cached_url = None

    def get_url(self):
        if self._view is None:
            return None

        if self._cached_url:
            return self._cached_url

        self._cached_url = url_for('%s.%s' % (self._view.endpoint, self._view._default_view))
        return self._cached_url

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
    def __init__(self, name, url=None, endpoint=None, category=None):
        super(MenuLink, self).__init__(name)

        self.category = category

        self.url = url
        self.endpoint = endpoint

    def get_url(self):
        return self.url or url_for(self.endpoint)
