import typing
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
    folder: typing.Literal["bootstrap4", "tabler"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")

TablerTheme = partial(BootstrapTheme, folder="tabler")
