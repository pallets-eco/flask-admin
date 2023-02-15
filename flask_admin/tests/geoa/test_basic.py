from __future__ import unicode_literals
import json
import re


from flask_admin.contrib.geoa import ModelView
from flask_admin.contrib.geoa.fields import GeoJSONField
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape

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

    return GeoModel


def test_model():
    app, db, admin = setup()
    GeoModel = create_models(db)
    with app.app_context():
        db.create_all()
    GeoModel.query.delete()
    db.session.commit()

    view = ModelView(GeoModel, db.session)
    admin.add_view(view)

    assert view.model == GeoModel
    assert view._primary_key == 'id'

    # Verify form
    assert view._create_form_class.point.field_class == GeoJSONField
    assert view._create_form_class.point.kwargs['geometry_type'] == "POINT"
    assert view._create_form_class.line.field_class == GeoJSONField
    assert view._create_form_class.line.kwargs['geometry_type'] == "LINESTRING"
    assert view._create_form_class.polygon.field_class == GeoJSONField
    assert view._create_form_class.polygon.kwargs['geometry_type'] == "POLYGON"
    assert view._create_form_class.multi.field_class == GeoJSONField
    assert view._create_form_class.multi.kwargs['geometry_type'] == "MULTIPOINT"

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/geomodel/')
    assert rv.status_code == 200

    rv = client.get('/admin/geomodel/new/')
    assert rv.status_code == 200

    rv = client.post('/admin/geomodel/new/', data={
        "name": "test1",
        "point": '{"type": "Point", "coordinates": [125.8, 10.0]}',
        "line": '{"type": "LineString", "coordinates": [[50.2345, 94.2], [50.21, 94.87]]}',
        "polygon": ('{"type": "Polygon", "coordinates": [[[100.0, 0.0], [101.0, 0.0],'
                    ' [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]}'),
        "multi": '{"type": "MultiPoint", "coordinates": [[100.0, 0.0], [101.0, 1.0]]}',
    })
    assert rv.status_code == 302

    model = db.session.query(GeoModel).first()
    assert model.name == "test1"
    assert to_shape(model.point).geom_type == "Point"
    assert list(to_shape(model.point).coords) == [(125.8, 10.0,)]
    assert to_shape(model.line).geom_type == "LineString"
    assert list(to_shape(model.line).coords) == [(50.2345, 94.2), (50.21, 94.87)]
    assert to_shape(model.polygon).geom_type == "Polygon"
    assert list(to_shape(model.polygon).exterior.coords) == \
           [(100.0, 0.0), (101.0, 0.0), (101.0, 1.0), (100.0, 1.0), (100.0, 0.0)]
    assert to_shape(model.multi).geom_type == "MultiPoint"
    assert len(to_shape(model.multi).geoms) == 2
    assert list(to_shape(model.multi).geoms[0].coords) == [(100.0, 0.0)]
    assert list(to_shape(model.multi).geoms[1].coords) == [(101.0, 1.0)]

    rv = client.get('/admin/geomodel/')
    assert rv.status_code == 200

    html = rv.data.decode('utf-8')
    pattern = r'(.|\n)+({.*"type": ?"Point".*})</textarea>(.|\n)+'
    group = re.match(pattern, html).group(2)
    p = json.loads(group)
    assert p['coordinates'][0] == 125.8
    assert p['coordinates'][1] == 10.0

    url = '/admin/geomodel/edit/?id=%s' % model.id
    rv = client.get(url)
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert (r'{"type":"MultiPoint","coordinates":[[100,0],[101,1]]}</textarea>' in data or
            r'{&#34;type&#34;:&#34;MultiPoint&#34;,&#34;coordinates&#34;:[[100,0],[101,1]]}' in data)

    # rv = client.post(url, data={
    #     "name": "edited",
    #     "point": '{"type": "Point", "coordinates": [99.9, 10.5]}',
    #     "line": '',  # set to NULL in the database
    # })
    # assert rv.status_code == 302
    #
    # model = db.session.query(GeoModel).first()
    # assert model.name == "edited"
    # assert to_shape(model.point).geom_type == "Point"
    # assert list(to_shape(model.point).coords) == [(99.9, 10.5])
    # assert to_shape(model.line) == None
    # assert to_shape(model.polygon).geom_type == "Polygon"
    # eq_(list(to_shape(model.polygon).exterior.coords),
    #     [(100.0, 0.0), (101.0, 0.0), (101.0, 1.0), (100.0, 1.0), (100.0, 0.0)])
    # assert to_shape(model.multi).geom_type == "MultiPoint"
    # assert len(to_shape(model.multi).geoms) == 2
    # assert list(to_shape(model.multi).geoms[0].coords) == [(100.0, 0.0])
    # assert list(to_shape(model.multi).geoms[1].coords) == [(101.0, 1.0])

    url = '/admin/geomodel/delete/?id=%s' % model.id
    rv = client.post(url)
    assert rv.status_code == 302
    assert db.session.query(GeoModel).count() == 0


def test_none():
    app, db, admin = setup()
    GeoModel = create_models(db)
    with app.app_context():
        db.create_all()
    GeoModel.query.delete()
    db.session.commit()

    view = ModelView(GeoModel, db.session)
    admin.add_view(view)

    # Make some test clients
    client = app.test_client()

    rv = client.post('/admin/geomodel/new/', data={
        "name": "test1",
    })
    assert rv.status_code == 302

    model = db.session.query(GeoModel).first()

    url = '/admin/geomodel/edit/?id=%s' % model.id
    rv = client.get(url)
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert (r' name="point"></textarea>' in data or
            ' name="point">\n</textarea>' in data or
            ' name="point">\r\n</textarea>' in data)
