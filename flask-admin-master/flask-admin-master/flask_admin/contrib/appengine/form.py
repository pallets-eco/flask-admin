from wtforms_appengine.ndb import ModelConverter
from .fields import GeoPtPropertyField
from flask_admin.model.form import converts


class AdminModelConverter(ModelConverter):
    @converts('GeoPt')
    def convert_GeoPtProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.GeoPtProperty``."""
        return GeoPtPropertyField(**kwargs)
