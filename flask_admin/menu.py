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
        class_name: t.Optional[str] = None,
        icon_type: t.Optional[str] = None,
        icon_value: t.Optional[str] = None,
        target: t.Optional[str] = None,
    ) -> None:
        self.name = name
        self.class_name: str = class_name if class_name is not None else ""
        self.icon_type = icon_type
        self.icon_value = icon_value
        self.target = target

        self.parent: t.Optional[BaseMenu] = None
        self._children: list[BaseMenu] = []

    def add_child(self, menu: "BaseMenu") -> None:
        # TODO: Check if menu item is already assigned to some parent
        menu.parent = self
        self._children.append(menu)

    def get_url(self) -> t.Optional[str]:
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

    def get_icon_type(self) -> t.Optional[str]:
        return self.icon_type

    def get_icon_value(self) -> t.Optional[str]:
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

    def get_url(self) -> t.Optional[str]:
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
        self._cached_url: t.Optional[str] = None

        view.menu = self

    def get_url(self) -> t.Optional[str]:
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
        url: t.Optional[str] = None,
        endpoint: t.Optional[str] = None,
        category: t.Optional[str] = None,
        class_name: t.Optional[str] = None,
        icon_type: t.Optional[str] = None,
        icon_value: t.Optional[str] = None,
        target: t.Optional[str] = None,
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
