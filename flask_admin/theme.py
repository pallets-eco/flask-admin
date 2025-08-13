import os
import typing
from dataclasses import dataclass
from functools import partial


@dataclass
class Theme:
    folder: str  # The templates folder name to use
    base_template: str


def get_allowed_swatches(folder: str) -> list[str]:
    base = os.path.dirname(__file__)
    # Directory where all swatches for the given folder are stored
    swatches_dir = os.path.join(base, "static", "bootstrap", folder, "swatch")

    allowed_swatches = []
    try:
        for swatch_name in os.listdir(swatches_dir):
            swatch_path = os.path.join(swatches_dir, swatch_name)
            swatch_file = os.path.join(swatch_path, "bootstrap.min.css")

            # A swatch is valid if the directory exists and
            # contains bootstrap.min.css
            if os.path.isdir(swatch_path) and os.path.isfile(swatch_file):
                allowed_swatches.append(swatch_name)

        # Always add 'default' if not present
        if "default" not in allowed_swatches:
            allowed_swatches.append("default")
    except Exception:
        pass

    return allowed_swatches


@dataclass
class BootstrapTheme(Theme):
    folder: typing.Literal["bootstrap4", "bootstrap5"]
    base_template: str = "admin/base.html"
    swatch: str = "default"
    fluid: bool = False

    def __post_init__(self):
        allowed_swatches = get_allowed_swatches(self.folder)
        if self.swatch not in allowed_swatches:
            raise ValueError(
                f"Invalid swatch '{self.swatch}' for {self.folder}. "
                f"Allowed: {allowed_swatches}"
            )


Bootstrap4Theme = partial(BootstrapTheme, folder="bootstrap4")
Bootstrap5Theme = partial(BootstrapTheme, folder="bootstrap5")
