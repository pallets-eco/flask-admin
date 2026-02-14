import json
import re

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from flask_admin.contrib.geoa import ModelView
from flask_admin.contrib.geoa.fields import GeoJSONField


def create_models(sqla_db_ext):
    class GeoModel(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "geo_model"
        id = Column(Integer, primary_key=True)
        name = Column(String(20))
        point = Column(Geometry("POINT"))
        line = Column(Geometry("LINESTRING"))
        polygon = Column(Geometry("POLYGON"))
        multi = Column(Geometry("MULTIPOINT"))

        def __str__(self):
            return self.name

    return GeoModel


def test_model(app, sqla_db_ext, admin, session_or_db):
    GeoModel = create_models(sqla_db_ext)
    with app.app_context():
        sqla_db_ext.create_all()
    sqla_db_ext.db.session.query(GeoModel).delete()
    sqla_db_ext.db.session.commit()

    param = sqla_db_ext.db if session_or_db == "session" else sqla_db_ext.db.session
    view = ModelView(GeoModel, param)
    admin.add_view(view)

    assert view.model == GeoModel
    assert view._primary_key == "id"

    # Verify form
    assert view._create_form_class.point.field_class == GeoJSONField  # type: ignore[attr-defined]
    assert view._create_form_class.point.kwargs["geometry_type"] == "POINT"  # type: ignore[attr-defined]
    assert view._create_form_class.line.field_class == GeoJSONField  # type: ignore[attr-defined]
    assert view._create_form_class.line.kwargs["geometry_type"] == "LINESTRING"  # type: ignore[attr-defined]
    assert view._create_form_class.polygon.field_class == GeoJSONField  # type: ignore[attr-defined]
    assert view._create_form_class.polygon.kwargs["geometry_type"] == "POLYGON"  # type: ignore[attr-defined]
    assert view._create_form_class.multi.field_class == GeoJSONField  # type: ignore[attr-defined]
    assert view._create_form_class.multi.kwargs["geometry_type"] == "MULTIPOINT"  # type: ignore[attr-defined]

    # Make some test clients
    client = app.test_client()

    rv = client.get("/admin/geomodel/")
    assert rv.status_code == 200

    rv = client.get("/admin/geomodel/new/")
    assert rv.status_code == 200

    rv = client.post(
        "/admin/geomodel/new/",
        data={
            "name": "test1",
            "point": '{"type": "Point", "coordinates": [125.8, 10.0]}',
            "line": (
                '{"type": "LineString", '
                '"coordinates": [[50.2345, 94.2], [50.21, 94.87]]}'
            ),
            "polygon": (
                '{"type": "Polygon", "coordinates": [[[100.0, 0.0], [101.0, 0.0],'
                " [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]}"
            ),
            "multi": (
                '{"type": "MultiPoint", "coordinates": [[100.0, 0.0], [101.0, 1.0]]}'
            ),
        },
    )
    assert rv.status_code == 302

    model = sqla_db_ext.db.session.query(GeoModel).first()
    assert model.name == "test1"
    assert to_shape(model.point).geom_type == "Point"
    assert list(to_shape(model.point).coords) == [
        (
            125.8,
            10.0,
        )
    ]
    assert to_shape(model.line).geom_type == "LineString"
    assert list(to_shape(model.line).coords) == [(50.2345, 94.2), (50.21, 94.87)]
    assert to_shape(model.polygon).geom_type == "Polygon"
    assert list(to_shape(model.polygon).exterior.coords) == [
        (100.0, 0.0),
        (101.0, 0.0),
        (101.0, 1.0),
        (100.0, 1.0),
        (100.0, 0.0),
    ]
    assert to_shape(model.multi).geom_type == "MultiPoint"
    assert len(to_shape(model.multi).geoms) == 2
    assert list(to_shape(model.multi).geoms[0].coords) == [(100.0, 0.0)]
    assert list(to_shape(model.multi).geoms[1].coords) == [(101.0, 1.0)]

    rv = client.get("/admin/geomodel/")
    assert rv.status_code == 200

    html = rv.data.decode("utf-8")
    pattern = r'(.|\n)+({.*"type": ?"Point".*})</textarea>(.|\n)+'
    group = re.match(pattern, html).group(2)  # type: ignore[union-attr]
    p = json.loads(group)
    assert p["coordinates"][0] == 125.8
    assert p["coordinates"][1] == 10.0

    url = f"/admin/geomodel/edit/?id={model.id}"
    rv = client.get(url)
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert (
        r'{"type":"MultiPoint","coordinates":[[100,0],[101,1]]}</textarea>' in data
        or (
            r"{&#34;type&#34;:&#34;MultiPoint&#34"
            r";,&#34;coordinates&#34;:[[100,0],[101,1]]}"
        )
        in data
    )

    url = f"/admin/geomodel/delete/?id={model.id}"
    rv = client.post(url)
    assert rv.status_code == 302
    assert sqla_db_ext.db.session.query(GeoModel).count() == 0


def test_none(app, sqla_db_ext, admin, session_or_db):
    GeoModel = create_models(sqla_db_ext)
    with app.app_context():
        sqla_db_ext.create_all()
    sqla_db_ext.db.session.query(GeoModel).delete()
    sqla_db_ext.db.session.commit()

    param = sqla_db_ext.db if session_or_db == "session" else sqla_db_ext.db.session
    view = ModelView(GeoModel, param)
    admin.add_view(view)

    # Make some test clients
    client = app.test_client()

    rv = client.post(
        "/admin/geomodel/new/",
        data={
            "name": "test1",
        },
    )
    assert rv.status_code == 302

    model = sqla_db_ext.db.session.query(GeoModel).first()

    url = f"/admin/geomodel/edit/?id={model.id}"
    rv = client.get(url)
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert (
        r' name="point"></textarea>' in data
        or ' name="point">\n</textarea>' in data
        or ' name="point">\r\n</textarea>' in data
    )
