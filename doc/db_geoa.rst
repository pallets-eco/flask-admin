GeoAlchemy backend
==================

If you want to store spatial information in a GIS database, Flask-Admin has
you covered. The `GeoAlchemy`_ backend extends the SQLAlchemy backend (just as
GeoAlchemy extends SQLAlchemy) to give you a pretty and functional map-based
editor for your admin pages.

Notable features:

 - Uses the amazing `Leaflet`_ Javascript library for displaying maps,
   with map data from `Mapbox`_
 - Uses `Leaflet.Draw`_ for editing geographic information interactively,
   including points, lines, and polygons
 - Graceful fallback to editing `GeoJSON`_ data in a ``<textarea>``, if the
   user has turned off Javascript
 - Works with a `Geometry`_ SQL field that is integrated with `Shapely`_ objects

Getting Started
---------------

GeoAlchemy is based on SQLAlchemy, so you'll need to complete the "getting started"
directions for SQLAlchemy backend first. For GeoAlchemy, you'll also need a
map ID from `Mapbox`_, a map tile provider. (Don't worry, their basic plan
is free, and works quite well.) Then, just include the map ID in your application
settings::

    app = Flask(__name__)
    app.config['MAPBOX_MAP_ID'] = "example.abc123"

.. note::
  Leaflet supports loading map tiles from any arbitrary map tile provider, but
  at the moment, Flask-Admin only supports Mapbox. If you want to use other
  providers, make a pull request!

Creating simple model
---------------------

GeoAlchemy comes with a `Geometry`_ field that is carefully divorced from the
`Shapely`_ library. Flask-Admin will use this field so that there are no 
changes necessary to other code. ``ModelView`` should be imported from 
``geoa`` rather than the one imported from ``sqla``::

    from geoalchemy2 import Geometry
    from flask.ext.admin.contrib.geoa import ModelView

    # .. flask initialization
    db = SQLAlchemy(app)

    class Location(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), unique=True)
        point = db.Column(Geometry("POINT"))

    if __name__ == '__main__':
        admin = Admin(app)
        admin.add_view(ModelView(User, db.session))

        db.create_all()
        app.run('0.0.0.0', 8000)

Limitations
-----------

There's currently no way to sort, filter, or search on geometric fields
in the admin. It's not clear that there's a good way to do so.
If you have any ideas or suggestions, make a pull request!

.. _GeoAlchemy: http://geoalchemy-2.readthedocs.org/
.. _Leaflet: http://leafletjs.com/
.. _Leaflet.Draw: https://github.com/Leaflet/Leaflet.draw
.. _Shapely: http://toblerity.org/shapely/
.. _Mapbox: https://www.mapbox.com/
.. _GeoJSON: http://geojson.org/
.. _Geometry: http://geoalchemy-2.readthedocs.org/en/latest/types.html#geoalchemy2.types.Geometry
