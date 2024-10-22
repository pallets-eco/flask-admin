import typing as t
from dataclasses import dataclass
from functools import partial


class Theme(t.Protocol):
    folder: str  # The templates folder name to use
    base_template: str


class Bootstrap(t.Protocol):
    swatch: str = "default"
    fluid: bool = False


@dataclass
class BootstrapTheme(Theme, Bootstrap):
    folder: t.Literal["bootstrap4"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")
