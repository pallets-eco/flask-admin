from mongoengine.base import get_document

from werkzeug.datastructures import FileStorage

from wtforms import fields

try:
    from wtforms.fields.core import _unset_value as unset_value
except ImportError:
    from wtforms.utils import unset_value

from . import widgets
from flask_admin.model.fields import InlineFormField


def is_empty(file_object):
    file_object.seek(0)
    first_char = file_object.read(1)
    file_object.seek(0)
    return not bool(first_char)


class ModelFormField(InlineFormField):
    """
        Customized ModelFormField for MongoEngine EmbeddedDocuments.
    """
    def __init__(self, model, view, form_class, form_opts=None, **kwargs):
        super(ModelFormField, self).__init__(form_class, **kwargs)

        self.model = model
        if isinstance(self.model, str):
            self.model = get_document(self.model)

        self.view = view
        self.form_opts = form_opts

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        is_created = candidate is None
        if is_created:
            candidate = self.model()
            setattr(obj, name, candidate)

        self.form.populate_obj(candidate)

        self.view._on_model_change(self.form, candidate, is_created)


class MongoFileField(fields.FileField):
    """
        GridFS file field.
    """
    widget = widgets.MongoFileInput()

    def __init__(self, label=None, validators=None, **kwargs):
        super(MongoFileField, self).__init__(label, validators, **kwargs)

        self._should_delete = False

    def process(self, formdata, data=unset_value):
        if formdata:
            marker = '_%s-delete' % self.name
            if marker in formdata:
                self._should_delete = True

        return super(MongoFileField, self).process(formdata, data)

    def populate_obj(self, obj, name):
        field = getattr(obj, name, None)
        if field is not None:
            # If field should be deleted, clean it up
            if self._should_delete:
                field.delete()
                return

            if isinstance(self.data, FileStorage) and not is_empty(self.data.stream):
                if not field.grid_id:
                    func = field.put
                else:
                    func = field.replace

                func(self.data.stream,
                     filename=self.data.filename,
                     content_type=self.data.content_type)


class MongoImageField(MongoFileField):
    """
        GridFS image field.
    """

    widget = widgets.MongoImageInput()
