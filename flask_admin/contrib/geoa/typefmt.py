from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from markupsafe import Markup
from sqlalchemy import func
from wtforms.widgets import html_params

from flask_admin.contrib.sqla.typefmt import DEFAULT_FORMATTERS as BASE_FORMATTERS


def geom_formatter(view, value, name) -> str:
    kwargs = {
        "data-role": "leaflet",
        "disabled": "disabled",
        "data-width": 100,
        "data-height": 70,
        "data-geometry-type": to_shape(value).geom_type,
        "data-zoom": 15,
    }
    # html_params will serialize None as a string literal "None" so only put
    # tile-layer-url and tile-layer-attribution in kwargs when they have a meaningful
    # value. flask_admin/static/admin/js/form.js uses its default values when these
    # are not passed as textarea attributes.
    if view.tile_layer_url:
        kwargs["data-tile-layer-url"] = view.tile_layer_url
    if view.tile_layer_attribution:
        kwargs["data-tile-layer-attribution"] = view.tile_layer_attribution
    params = html_params(**kwargs)

    if value.srid == -1:
        value.srid = 4326

    geojson = (
        view.session.query(view.model).with_entities(func.ST_AsGeoJSON(value)).scalar()
    )
    return Markup(f"<textarea {params}>{geojson}</textarea>")


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS[WKBElement] = geom_formatter
