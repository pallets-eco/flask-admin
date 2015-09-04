from __future__ import unicode_literals
from nose.tools import eq_, ok_

from flask_admin.contrib.geoa import ModelView
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from flask_admin.contrib.geoa.fields import GeoJSONField

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
    point_opt_1 = '>{"type": "Point", "coordinates": [125.8, 10.0]}</textarea>'
    point_opt_2 = '>{"coordinates": [125.8, 10.0], "type": "Point"}</textarea>'
    point_opt_3 = '>{"type":"Point","coordinates":[125.8,10]}</textarea>'
    html = rv.data.decode('utf-8')
    ok_(point_opt_1 in html or point_opt_2 in html or point_opt_3 in html, html)

    url = '/admin/geomodel/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    #rv = client.post(url, data={
    #    "name": "edited",
    #    "point": '{"type": "Point", "coordinates": [99.9, 10.5]}',
    #    "line": '',  # set to NULL in the database
    #})
    #eq_(rv.status_code, 302)
    #
    #model = db.session.query(GeoModel).first()
    #eq_(model.name, "edited")
    #eq_(to_shape(model.point).geom_type, "Point")
    #eq_(list(to_shape(model.point).coords), [(99.9, 10.5)])
    #eq_(to_shape(model.line), None)
    #eq_(to_shape(model.polygon).geom_type, "Polygon")
    #eq_(list(to_shape(model.polygon).exterior.coords),
    #    [(100.0, 0.0), (101.0, 0.0), (101.0, 1.0), (100.0, 1.0), (100.0, 0.0)])
    #eq_(to_shape(model.multi).geom_type, "MultiPoint")
    #eq_(len(to_shape(model.multi).geoms), 2)
    #eq_(list(to_shape(model.multi).geoms[0].coords), [(100.0, 0.0)])
    #eq_(list(to_shape(model.multi).geoms[1].coords), [(101.0, 1.0)])

    url = '/admin/geomodel/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(db.session.query(GeoModel).count(), 0)
