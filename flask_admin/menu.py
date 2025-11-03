import typing as t

from flask import url_for

from flask_admin._types import T_MODEL_VIEW
from flask_admin._types import T_VIEW


class BaseMenu:
    """
    Base menu item
    """

    def __init__(
        self,
        name: str,
        class_name: str | None = None,
        icon_type: str | None = None,
        icon_value: str | None = None,
        target: str | None = None,
    ) -> None:
        self.name = name
        self.class_name: str = class_name if class_name is not None else ""
        self.icon_type = icon_type
        self.icon_value = icon_value
        self.target = target

        self.parent: BaseMenu | None = None
        self._children: list[BaseMenu] = []

    def add_child(self, menu: "BaseMenu") -> None:
        # TODO: Check if menu item is already assigned to some parent
        menu.parent = self
        self._children.append(menu)

    def get_url(self) -> str | None:
        raise NotImplementedError()

    def is_category(self) -> bool:
        return False

    def is_active(self, view: T_MODEL_VIEW) -> bool:
        for c in self._children:
            if c.is_active(view):
                return True

        return False

    def get_class_name(self) -> str:
        return self.class_name

    def get_icon_type(self) -> str | None:
        return self.icon_type

    def get_icon_value(self) -> str | None:
        return self.icon_value

    def is_visible(self) -> bool:
        return True

    def is_accessible(self) -> bool:
        return True

    def get_children(self) -> list["BaseMenu"]:
        return [c for c in self._children if c.is_accessible() and c.is_visible()]


class MenuCategory(BaseMenu):
    """
    Menu category item.
    """

    def get_url(self) -> str | None:
        return None

    def is_category(self) -> bool:
        return True

    def is_visible(self) -> bool:
        for c in self._children:
            if c.is_visible():
                return True

        return False

    def is_accessible(self) -> bool:
        for c in self._children:
            if c.is_accessible():
                return True

        return False


class MenuView(BaseMenu):
    """
    Admin view menu item
    """

    def __init__(
        self,
        name: str,
        view: T_VIEW = None,  # type: ignore[assignment]
        cache: bool = True,
    ) -> None:
        super().__init__(
            name,
            class_name=view.menu_class_name,
            icon_type=view.menu_icon_type,
            icon_value=view.menu_icon_value,
        )

        self._view = view
        self._cache = cache
        self._cached_url: str | None = None

        view.menu = self

    def get_url(self) -> str | None:
        if self._view is None:
            return None

        if self._cached_url:
            return self._cached_url

        url = self._view.get_url(
            f"{self._view.endpoint}.{self._view._default_view}"  # type: ignore[attr-defined]
        )

        if self._cache:
            self._cached_url = url

        return url

    def is_active(self, view: T_MODEL_VIEW) -> bool:
        if view == self._view:
            return True

        return super().is_active(view)

    def is_visible(self) -> bool:
        if self._view is None:
            return False

        return self._view.is_visible()

    def is_accessible(self) -> bool:
        if self._view is None:
            return False

        return self._view.is_accessible()


class MenuLink(BaseMenu):
    """
    Link item
    """

    def __init__(
        self,
        name: str,
        url: str | None = None,
        endpoint: str | None = None,
        category: str | None = None,
        class_name: str | None = None,
        icon_type: str | None = None,
        icon_value: str | None = None,
        target: str | None = None,
    ) -> None:
        super().__init__(name, class_name, icon_type, icon_value, target)

        self.category = category

        self.url = url
        self.endpoint = endpoint

    def get_url(self) -> str:
        return self.url or url_for(self.endpoint)  # type: ignore[arg-type]


class SubMenuCategory(MenuCategory):
    def __init__(self, *args: str, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.class_name += " dropdown-submenu dropright"


class MenuDivider(MenuLink):
    """
    Bootstrap Menu divider item
    Usage:
      admin = Admin(app, ...)
      admin.add_menu_item(MenuDivider(), target_category='Category1')
    """

    def __init__(self, class_name=""):
        class_name = "dropdown-divider" + (" " + class_name if class_name else "")
        super().__init__("divider", class_name=class_name)

    def get_url(self):
        return None

    def is_visible(self):
        # Return True/False depending on your use-case
        return True
