import typing
from dataclasses import dataclass
from functools import partial


@dataclass
class Theme:
    folder: str  # The templates folder name to use
    base_template: str


@dataclass
class BootstrapTheme(Theme):
    folder: typing.Literal["bootstrap4", "tabler"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")

TablerTheme = partial(BootstrapTheme, folder="tabler")
