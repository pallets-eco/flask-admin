# flake8: noqa
try:
    import geoalchemy2
    import shapely
except ImportError:
    raise Exception('Please install geoalchemy2 and shapely in order to use geoalchemy integration')

from .view import ModelView
