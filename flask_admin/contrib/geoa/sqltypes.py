from geoalchemy2 import Geometry as BaseGeometry
from geoalchemy2.shape import to_shape


class Geometry(BaseGeometry):
    """
    PostGIS datatype that can convert directly to/from Shapely objects,
    without worrying about WKTElements or WKBElements.
    """
    def result_processor(self, dialect, coltype):
        to_wkbelement = super(Geometry, self).result_processor(dialect, coltype)

        def process(value):
            if value:
                return to_shape(to_wkbelement(value))
            else:
                return None
        return process

    def bind_processor(self, dialect):
        from_wktelement = super(Geometry, self).bind_processor(dialect)

        def process(value):
            if value:
                return from_wktelement(value.wkt)
            else:
                return None
        return process
