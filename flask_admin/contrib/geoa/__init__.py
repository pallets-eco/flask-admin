# flake8: noqa
try:
    import geoalchemy2
    import shapely
except ImportError:
    raise Exception(
        "Could not import `geoalchemy2` or `shapely`. "
        "Enable `geoalchemy` integration by installing `flask-admin[geoalchemy]`"
    )

from .view import ModelView
