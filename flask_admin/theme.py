import typing
from dataclasses import dataclass
from functools import partial


@dataclass
class Theme:
    folder: str  # The templates folder name to use


@dataclass
class BootstrapTheme(Theme):
    folder: typing.Literal['bootstrap2', 'bootstrap3', 'bootstrap4']
    swatch: str = 'default'
    fluid: bool = False


Bootstrap2Theme = partial(BootstrapTheme, folder='bootstrap2')
Bootstrap3Theme = partial(BootstrapTheme, folder='bootstrap3')
Bootstrap4Theme = partial(BootstrapTheme, folder='bootstrap4')
