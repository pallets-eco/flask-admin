from typing import get_type_hints

from flask_admin.theme import Bootstrap4Theme
from flask_admin.theme import BootstrapTheme


def test_bootstrap4_defaults() -> None:
    theme = Bootstrap4Theme()

    assert isinstance(theme, BootstrapTheme)
    assert theme.folder == "bootstrap4"
    assert theme.base_template == "admin/base.html"
    assert theme.swatch == "default"
    assert theme.fluid is False


def test_bootstrap4_custom_options() -> None:
    theme = Bootstrap4Theme(
        folder="bootstrap4",
        base_template="custom.html",
        swatch="cerulean",
        fluid=True,
    )

    assert theme.folder == "bootstrap4"
    assert theme.base_template == "custom.html"
    assert theme.swatch == "cerulean"
    assert theme.fluid is True


def test_bootstrap4_constructor_type_hints() -> None:
    hints = get_type_hints(Bootstrap4Theme.__init__)

    assert hints["base_template"] is str
    assert hints["swatch"] is str
    assert hints["fluid"] is bool
