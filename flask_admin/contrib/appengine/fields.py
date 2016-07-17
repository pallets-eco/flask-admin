from wtforms.fields import TextField
from google.appengine.ext import ndb

import decimal

class GeoPtPropertyField(TextField):
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
