import typing
from dataclasses import dataclass
from dataclasses import field


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

    folder: typing.Literal["bootstrap4"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False


@dataclass
class Bootstrap4Theme(BootstrapTheme):
    """Bootstrap 4 theme with typed constructor options.

    .. versionchanged:: unreleased
        Replaced the partial constructor with a dataclass subclass.
        The ``folder`` constructor argument is no longer accepted. Use
        :class:`Theme` or a custom theme subclass for a different template folder.
    """

    folder: typing.Literal["bootstrap4"] = field(default="bootstrap4", init=False)
