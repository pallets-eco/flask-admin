from __future__ import unicode_literals
import json
import re

from flask_admin.contrib.geoa import ModelView
from flask_admin.contrib.geoa.fields import GeoJSONField
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from nose.tools import eq_

from . import setup


def create_models(db):
    class GeoModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20))
        point = db.Column(Geometry("POINT"))
        line = db.Column(Geometry("LINESTRING"))
        polygon = db.Column(Geometry("POLYGON"))
        multi = db.Column(Geometry("MULTIPOINT"))

        def __unicode__(self):
            return self.name

    db.create_all()

    return GeoModel


def test_model():
    app, db, admin = setup()
    GeoModel = create_models(db)
    db.create_all()
    GeoModel.query.delete()
    db.session.commit()

    view = ModelView(GeoModel, db.session)
    admin.add_view(view)

    eq_(view.model, GeoModel)
    eq_(view._primary_key, 'id')

    # Verify form
    eq_(view._create_form_class.point.field_class, GeoJSONField)
    eq_(view._create_form_class.point.kwargs['geometry_type'], "POINT")
    eq_(view._create_form_class.line.field_class, GeoJSONField)
    eq_(view._create_form_class.line.kwargs['geometry_type'], "LINESTRING")
    eq_(view._create_form_class.polygon.field_class, GeoJSONField)
    eq_(view._create_form_class.polygon.kwargs['geometry_type'], "POLYGON")
    eq_(view._create_form_class.multi.field_class, GeoJSONField)
    eq_(view._create_form_class.multi.kwargs['geometry_type'], "MULTIPOINT")

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/geomodel/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/geomodel/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/geomodel/new/', data={
        "name": "test1",
        "point": '{"type": "Point", "coordinates": [125.8, 10.0]}',
        "line": '{"type": "LineString", "coordinates": [[50.2345, 94.2], [50.21, 94.87]]}',
        "polygon": '{"type": "Polygon", "coordinates": [[[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]}',
        "multi": '{"type": "MultiPoint", "coordinates": [[100.0, 0.0], [101.0, 1.0]]}',
    })
    eq_(rv.status_code, 302)

    model = db.session.query(GeoModel).first()
    eq_(model.name, "test1")
    eq_(to_shape(model.point).geom_type, "Point")
    eq_(list(to_shape(model.point).coords), [(125.8, 10.0)])
    eq_(to_shape(model.line).geom_type, "LineString")
    eq_(list(to_shape(model.line).coords), [(50.2345, 94.2), (50.21, 94.87)])
    eq_(to_shape(model.polygon).geom_type, "Polygon")
    eq_(list(to_shape(model.polygon).exterior.coords),
        [(100.0, 0.0), (101.0, 0.0), (101.0, 1.0), (100.0, 1.0), (100.0, 0.0)])
    eq_(to_shape(model.multi).geom_type, "MultiPoint")
    eq_(len(to_shape(model.multi).geoms), 2)
    eq_(list(to_shape(model.multi).geoms[0].coords), [(100.0, 0.0)])
    eq_(list(to_shape(model.multi).geoms[1].coords), [(101.0, 1.0)])

    rv = client.get('/admin/geomodel/')
    eq_(rv.status_code, 200)

    html = rv.data.decode('utf-8')
    pattern = r'(.|\n)+({.*"type": ?"Point".*})</textarea>(.|\n)+'
    group = re.match(pattern, html).group(2)
    p = json.loads(group)
    eq_(p['coordinates'][0], 125.8)
    eq_(p['coordinates'][1], 10.0)

    url = '/admin/geomodel/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    # rv = client.post(url, data={
    #     "name": "edited",
    #     "point": '{"type": "Point", "coordinates": [99.9, 10.5]}',
    #     "line": '',  # set to NULL in the database
    # })
    # eq_(rv.status_code, 302)
    #
    # model = db.session.query(GeoModel).first()
    # eq_(model.name, "edited")
    # eq_(to_shape(model.point).geom_type, "Point")
    # eq_(list(to_shape(model.point).coords), [(99.9, 10.5)])
    # eq_(to_shape(model.line), None)
    # eq_(to_shape(model.polygon).geom_type, "Polygon")
    # eq_(list(to_shape(model.polygon).exterior.coords),
    #     [(100.0, 0.0), (101.0, 0.0), (101.0, 1.0), (100.0, 1.0), (100.0, 0.0)])
    # eq_(to_shape(model.multi).geom_type, "MultiPoint")
    # eq_(len(to_shape(model.multi).geoms), 2)
    # eq_(list(to_shape(model.multi).geoms[0].coords), [(100.0, 0.0)])
    # eq_(list(to_shape(model.multi).geoms[1].coords), [(101.0, 1.0)])

    url = '/admin/geomodel/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(db.session.query(GeoModel).count(), 0)


def test_mapbox_fix_point_coordinates():
    app, db, admin = setup()
    app.config['MAPBOX_FIX_COORDINATES_ORDER'] = True
    GeoModel = create_models(db)
    db.create_all()
    GeoModel.query.delete()
    db.session.commit()

    view = ModelView(GeoModel, db.session)
    admin.add_view(view)

    # Make some test clients
    client = app.test_client()

    rv = client.post('/admin/geomodel/new/', data={
        "name": "test1",
        "point": '{"type": "Point", "coordinates": [125.8, 10.0]}',
        "line": '{"type": "LineString", "coordinates": [[50.2345, 94.2], [50.21, 94.87]]}',
        "polygon": '{"type": "Polygon", "coordinates": [[[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]}',
        "multi": '{"type": "MultiPoint", "coordinates": [[100.0, 0.0], [101.0, 1.0]]}',
    })

    model = db.session.query(GeoModel).first()
    # Notice how the coordinates are reversed here, i.e. longitude first which
    # is the way it's stored in PostGIS columns.
    eq_(list(to_shape(model.point).coords), [(10.0, 125.8)])
    eq_(list(to_shape(model.line).coords), [(94.2, 50.2345), (94.87, 50.21)])
    eq_(list(to_shape(model.polygon).exterior.coords),
        [(0.0, 100.0), (0.0, 101.0), (1.0, 101.0), (1.0, 100.0), (0.0, 100.0)])
    eq_(list(to_shape(model.multi).geoms[0].coords), [(0.0, 100.0)])
    eq_(list(to_shape(model.multi).geoms[1].coords), [(1.0, 101.0)])

    rv = client.get('/admin/geomodel/')
    eq_(rv.status_code, 200)

    html = rv.data.decode('utf-8')
    pattern = r'(.|\n)+({.*"type": ?"Point".*})</textarea>(.|\n)+'
    group = re.match(pattern, html).group(2)
    p = json.loads(group)

    # Reversed order again, so that it's parsed correctly by leaflet
    eq_(p['coordinates'][0], 10.0)
    eq_(p['coordinates'][1], 125.8)
