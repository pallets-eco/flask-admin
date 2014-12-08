import json
from wtforms.fields import TextAreaField
from shapely.geometry import shape, mapping
from .widgets import LeafletWidget
from sqlalchemy import func
import geoalchemy2
#from types import NoneType
#from .. import db how do you get db.session in a Field?


class JSONField(TextAreaField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if self.data:
            return self.data
        return ""

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]
            if not value:
                self.data = None
                return
            try:
                self.data = self.from_json(value)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Invalid JSON'))

    def to_json(self, obj):
        return json.dumps(obj)

    def from_json(self, data):
        return json.loads(data)


class GeoJSONField(JSONField):
    widget = LeafletWidget()
    
    def __init__(self, label=None, validators=None, geometry_type="GEOMETRY", srid='-1', session=None, **kwargs):
        super(GeoJSONField, self).__init__(label, validators, **kwargs)
        self.web_srid = 4326
        self.srid = srid
        if self.srid is -1:
        	self.transform_srid = self.web_srid
        else:
        	self.transform_srid = self.srid
        self.geometry_type = geometry_type.upper()
        self.session = session
    
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if type(self.data) is geoalchemy2.elements.WKBElement:
            if self.srid is -1:
                self.data = self.session.scalar(func.ST_AsGeoJson(self.data))
            else:
                self.data = self.session.scalar(func.ST_AsGeoJson(func.ST_Transform(self.data, self.web_srid)))
        return super(GeoJSONField, self)._value()
    
    def process_formdata(self, valuelist):
        super(GeoJSONField, self).process_formdata(valuelist)
        if str(self.data) is '':
            self.data = None
        if self.data is not None:
            web_shape = self.session.scalar(func.ST_AsText(func.ST_Transform(func.ST_GeomFromText(shape(self.data).wkt, self.web_srid), self.transform_srid)))
            self.data = 'SRID='+str(self.srid)+';'+str(web_shape)
