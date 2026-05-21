import json
import re
import typing as t

from flask import Flask
from geoalchemy2 import Geometry
from geoalchemy2 import WKBElement
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from shapely import MultiPoint
from shapely import Polygon
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from flask_admin import Admin
from flask_admin.contrib.geoa import ModelView
from flask_admin.contrib.geoa.fields import GeoJSONField
from flask_admin.tests.conftest import skip_or_return_session_or_db
from flask_admin.tests.conftest import T_ANY_SQLA_PROVIDER


class GeoModelProtocol(t.Protocol):
    id: int
    name: str
    point: WKBElement | WKTElement
    line: WKBElement | WKTElement
    polygon: WKBElement | WKTElement
    multi: WKBElement | WKTElement


def create_models(sqla_db_ext: T_ANY_SQLA_PROVIDER) -> type[GeoModelProtocol]:
    class GeoModel(sqla_db_ext.Base):  # type: ignore[misc,name-defined]
        __tablename__ = "geo_model"
        id = Column(Integer, primary_key=True)
        name = Column(String(20))
        point = Column(Geometry("POINT"))
        line = Column(Geometry("LINESTRING"))
        polygon = Column(Geometry("POLYGON"))
        multi = Column(Geometry("MULTIPOINT"))

        def __str__(self) -> str:
            return self.name  # type: ignore[return-value]

    return GeoModel


def test_model(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: t.Literal["session", "db"],
) -> None:
    geo_model = create_models(sqla_db_ext)
    with app.app_context():
        sqla_db_ext.create_all()
    sqla_db_ext.db.session.query(geo_model).delete()
    sqla_db_ext.db.session.commit()

    param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
    view = ModelView(geo_model, param)
    admin.add_view(view)

    assert view.model == geo_model
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

    model = sqla_db_ext.db.session.query(geo_model).first()
    assert model
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
    shape = to_shape(model.polygon)
    assert isinstance(shape, Polygon)
    assert list(shape.exterior.coords) == [
        (100.0, 0.0),
        (101.0, 0.0),
        (101.0, 1.0),
        (100.0, 1.0),
        (100.0, 0.0),
    ]
    shape = to_shape(model.multi)
    assert isinstance(shape, MultiPoint)
    assert len(shape.geoms) == 2
    assert list(shape.geoms[0].coords) == [(100.0, 0.0)]
    assert list(shape.geoms[1].coords) == [(101.0, 1.0)]

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
    assert sqla_db_ext.db.session.query(geo_model).count() == 0


def test_none(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: t.Literal["session", "db"],
) -> None:
    geo_model = create_models(sqla_db_ext)
    with app.app_context():
        sqla_db_ext.create_all()
    sqla_db_ext.db.session.query(geo_model).delete()
    sqla_db_ext.db.session.commit()

    param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
    view = ModelView(geo_model, param)
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

    model = sqla_db_ext.db.session.query(geo_model).first()

    assert model
    url = f"/admin/geomodel/edit/?id={model.id}"
    rv = client.get(url)
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert (
        r' name="point"></textarea>' in data
        or ' name="point">\n</textarea>' in data
        or ' name="point">\r\n</textarea>' in data
    )
