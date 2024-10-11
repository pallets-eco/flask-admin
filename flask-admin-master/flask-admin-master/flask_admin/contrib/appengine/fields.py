from wtforms.fields import StringField
from google.appengine.ext import ndb

import decimal


class GeoPtPropertyField(StringField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                lat, lon = valuelist[0].split(',')
                self.data = ndb.GeoPt(
                    decimal.Decimal(lat.strip()),
                    decimal.Decimal(lon.strip())
                )

            except (decimal.InvalidOperation, ValueError):
                raise ValueError('Not a valid coordinate location')
