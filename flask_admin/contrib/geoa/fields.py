import geoalchemy2
from shapely.geometry import shape
from sqlalchemy import func

from flask_admin.form import JSONField

from ..sqla._compat import get_deprecated_session
from ..sqla._compat import warn_session_deprecation
from ..sqla._types import T_SCOPED_SESSION
from ..sqla._types import T_SQLALCHEMY
from ..sqla._types import T_SQLALCHEMY_LITE
from .widgets import LeafletWidget


class GeoJSONField(JSONField):
    def __init__(
        self,
        label=None,
        validators=None,
        geometry_type="GEOMETRY",
        srid="-1",
        session: T_SCOPED_SESSION | T_SQLALCHEMY | T_SQLALCHEMY_LITE | None = None,
        tile_layer_url=None,
        tile_layer_attribution=None,
        **kwargs,
    ):
        self.widget = LeafletWidget(
            tile_layer_url=tile_layer_url, tile_layer_attribution=tile_layer_attribution
        )
        super().__init__(label, validators, **kwargs)
        self.web_srid = 4326
        self.srid = srid
        if self.srid == -1:
            self.transform_srid = self.web_srid
        else:
            self.transform_srid = self.srid
        self.geometry_type = geometry_type.upper()
        self.session = warn_session_deprecation(session)

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if type(self.data) is geoalchemy2.elements.WKBElement:  # type: ignore[comparison-overlap]
            session = get_deprecated_session(self.session)

            if self.srid == -1:
                return session.scalar(  # pyright: ignore[reportOptionalMemberAccess]
                    func.ST_AsGeoJSON(self.data)
                )
            else:
                return session.scalar(  # pyright: ignore[reportOptionalMemberAccess]
                    func.ST_AsGeoJSON(func.ST_Transform(self.data, self.web_srid))
                )
        else:
            return ""

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        if str(self.data) == "":
            self.data = None
        if self.data is not None:
            session = get_deprecated_session(self.session)
            web_shape = session.scalar(  # pyright: ignore[reportOptionalMemberAccess]
                func.ST_AsText(
                    func.ST_Transform(
                        func.ST_GeomFromText(shape(self.data).wkt, self.web_srid),  # type: ignore[arg-type]
                        self.transform_srid,
                    )
                )
            )
            self.data = "SRID=" + str(self.srid) + ";" + str(web_shape)
