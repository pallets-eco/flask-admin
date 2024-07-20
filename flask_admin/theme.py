from dataclasses import dataclass
import typing
from functools import partial


@dataclass
class Theme:
    folder: str  # The templates folder name to use
    base_template: str


@dataclass
class BootstrapTheme(Theme):
    folder: typing.Literal['bootstrap2', 'bootstrap3', 'bootstrap4']
    base_template: str = 'admin/base.html'
    swatch: str = 'default'
    fluid: bool = False


Bootstrap2Theme = partial(BootstrapTheme, folder='bootstrap2')
Bootstrap3Theme = partial(BootstrapTheme, folder='bootstrap3')
Bootstrap4Theme = partial(BootstrapTheme, folder='bootstrap4')
