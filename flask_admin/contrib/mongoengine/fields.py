from flask import request
from wtforms import fields

from . import widgets


class ModelFormField(fields.FormField):
    """
        Customized ModelFormField for MongoEngine EmbeddedDocuments.
    """
    def __init__(self, model, *args, **kwargs):
        super(ModelFormField, self).__init__(*args, **kwargs)

        self.model = model

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        if candidate is None:
            candidate = self.model()
            setattr(obj, name, candidate)

        self.form.populate_obj(candidate)


class MongoFileField(fields.FileField):
    widget = widgets.MongoFileInput()

    def populate_obj(self, obj, name):
        field = getattr(obj, name, None)
        if field is not None:
            data = request.files.get(self.name)

            print data.filename

            if data:
                if not field.grid_id:
                    field.put(data.stream,
                              filename=data.filename,
                              content_type=data.content_type)
                else:
                    field.replace(data.stream,
                                  filename=data.filename,
                                  content_type=data.content_type)
