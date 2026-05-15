import typing as t
from dataclasses import dataclass
from functools import partial


@dataclass
class Theme:
    folder: str  # The templates folder name to use
    base_template: str


@dataclass
class BootstrapTheme(Theme):
    """
    Bootstrap theme for Flask-Admin.

    Usage::

        t = Bootstrap4Theme(
            base_template='my_base.html', # relative your templates folder
            swatch='cerulean',
            fluid=True
        )
        admin = Admin(app, name='microblog', theme=t)
    """

    folder: t.Literal["bootstrap4"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False


TablerLayout = t.Literal["vertical", "fluid", "condensed"]


def _validate_choice(value: str, choices: tuple[str, ...]) -> None:
    if value not in choices:
        supported = ", ".join(choices)
        raise ValueError(f"Unsupported layout: {value}. Expected one of: {supported}")


@dataclass
class TablerUITheme(Theme):
    """
    Tabler 1.4.0 theme for Flask-Admin.

    Ships Tabler UI assets locally (CSS, JS, icon webfonts) so no CDN is
    required.

    Usage::
        admin = Admin(app, name="my app", theme=TablerTheme(layout="vertical"))
    """

    VALID_LAYOUTS = t.get_args(TablerLayout)

    folder: str = "tabler"
    base_template: str = "admin/base.html"

    layout: TablerLayout = "vertical"

    # Tabler UI theme settings — map directly to data-bs-* HTML attributes.
    # Defaults match Tabler's own defaults so existing deployments are unaffected.
    theme: str = "light"  # "light" | "dark"
    theme_primary: str = "blue"  # "blue" | "lime" | "azure" | "indigo" | …
    theme_base: str = "gray"  # "gray" | "neutral" | "slate" | "zinc" | "stone"
    theme_font: str = "sans-serif"  # "sans-serif" | "serif" | "monospace" | "comic"
    theme_radius: str = "1"  # "0" | "0.5" | "1" | "1.5" | "2"
    theme_use_cdn: bool = True  # From where to load tabler files

    def __post_init__(self) -> None:
        _validate_choice(self.layout, self.VALID_LAYOUTS)

    @property
    def is_sidebar_layout(self) -> bool:
        return self.layout == "vertical"

    @property
    def is_fluid_layout(self) -> bool:
        return self.layout == "fluid"

    @property
    def is_condensed_layout(self) -> bool:
        return self.layout == "condensed"

    @property
    def body_class(self) -> str:
        return "layout-fluid" if self.is_fluid_layout else ""

    @property
    def use_cdn(self) -> bool:
        return self.theme_use_cdn


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")
TablerTheme = partial(TablerUITheme, folder="tabler")
