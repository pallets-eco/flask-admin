import json
from wtforms.fields import TextAreaField
from shapely.geometry import shape, mapping
from .widgets import LeafletWidget


class JSONField(TextAreaField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if self.data:
            return self.to_json(self.data)
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

    def __init__(self, label=None, validators=None, geometry_type="GEOMETRY", **kwargs):
        super(GeoJSONField, self).__init__(label, validators, **kwargs)
        self.geometry_type = geometry_type.upper()

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if self.data:
            self.data = mapping(self.data)
        return super(GeoJSONField, self)._value()

    def process_formdata(self, valuelist):
        super(GeoJSONField, self).process_formdata(valuelist)
        if self.data:
            self.data = shape(self.data)
