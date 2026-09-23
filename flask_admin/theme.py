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
class TablerTheme(Theme):
    """
    Tabler 1.4.0 theme for Flask-Admin.

    Usage::
        admin = Admin(app,
                      name="my app",
                      theme=TablerTheme(
                                        layout="vertical",
                                        theme="light",
                                        theme_primary="blue",
                                        theme_base="gray",
                                        theme_font="sans-serif",
                                        theme_radius="1",
                                        )
                      )
    """

    VALID_LAYOUTS = t.get_args(TablerLayout)

    folder: str = "tabler"
    base_template: str = "admin/base.html"

    layout: TablerLayout = "vertical"

    # Tabler UI theme settings — map directly to data-bs-* HTML attributes.
    # Defaults match Tabler's own defaults so existing deployments are unaffected.
    theme: t.Literal["light", "dark"] = "light"
    theme_primary: t.Literal[
        "blue",
        "azure",
        "indigo",
        "purple",
        "pink",
        "red",
        "orange",
        "lime",
        "green",
        "teal",
        "cyan",
    ] = "blue"
    theme_base: t.Literal["gray", "neutral", "slate", "zinc", "stone"] = "gray"
    theme_font: t.Literal["sans-serif", "serif", "monospace", "comic"] = "sans-serif"
    theme_radius: t.Literal["0", "0.5", "1", "1.5", "2"] = "1"

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


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")
