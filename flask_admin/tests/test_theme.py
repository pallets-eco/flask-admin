import pytest

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
        base_template="custom.html",
        swatch="cerulean",
        fluid=True,
    )

    assert theme.folder == "bootstrap4"
    assert theme.base_template == "custom.html"
    assert theme.swatch == "cerulean"
    assert theme.fluid is True


@pytest.mark.parametrize("folder", ["bootstrap4", "bootstrap3"])
def test_bootstrap4_rejects_folder_argument(folder: str) -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument 'folder'"):
        Bootstrap4Theme(folder=folder)  # type: ignore[call-arg]
