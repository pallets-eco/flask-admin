from flask import request
from wtforms import fields
from wtforms.fields.core import _unset_value

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

    def __init__(self, label=None, validators=None, **kwargs):
        super(MongoFileField, self).__init__(label, validators, **kwargs)

        self.should_delete = False

    def process(self, formdata, data=_unset_value):
        if formdata:
            marker = '_%s-delete' % self.name
            if marker in formdata:
                self.should_delete = True

        return super(MongoFileField, self).process(formdata, data)

    def populate_obj(self, obj, name):
        field = getattr(obj, name, None)
        if field is not None:
            # If field should be deleted, clean it up
            if self.should_delete:
                field.delete()
                return

            data = request.files.get(self.name)

            if data:
                if not field.grid_id:
                    field.put(data.stream,
                              filename=data.filename,
                              content_type=data.content_type)
                else:
                    field.replace(data.stream,
                                  filename=data.filename,
                                  content_type=data.content_type)


class MongoImageField(MongoFileField):
    widget = widgets.MongoImageInput()
