from flask.ext.admin.contrib.sqla.typefmt import DEFAULT_FORMATTERS as BASE_FORMATTERS
import json
from jinja2 import Markup
from wtforms.widgets import html_params
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from sqlalchemy import func
from flask import current_app


def geom_formatter(view, value):
    params = html_params(**{
        "data-role": "leaflet",
        "disabled": "disabled",
        "data-width": 100,
        "data-height": 70,
        "data-geometry-type": to_shape(value).geom_type,
        "data-zoom": 15,
    })
    if value.srid is -1:
        geojson = current_app.extensions['sqlalchemy'].db.session.scalar(func.ST_AsGeoJson(value))
    else:
        geojson = current_app.extensions['sqlalchemy'].db.session.scalar(func.ST_AsGeoJson(value.ST_Transform( 4326)))
    return Markup('<textarea %s>%s</textarea>' % (params, geojson))


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS[WKBElement] = geom_formatter
