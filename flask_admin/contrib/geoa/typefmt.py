from flask.ext.admin.contrib.sqla.typefmt import DEFAULT_FORMATTERS as BASE_FORMATTERS
import json
from jinja2 import Markup
from wtforms.widgets import html_params
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry


def geom_formatter(view, value):
    params = html_params(**{
        "data-role": "leaflet",
        "disabled": "disabled",
        "data-width": 100,
        "data-height": 70,
        "data-geometry-type": value.geom_type,
        "data-zoom": 15,
    })
    geojson = json.dumps(mapping(value))
    return Markup('<textarea %s>%s</textarea>' % (params, geojson))


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS[BaseGeometry] = geom_formatter
