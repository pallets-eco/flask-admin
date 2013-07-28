import os
import os.path as op

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from jinja2 import escape

from wtforms import ValidationError, fields
from wtforms.widgets import HTMLString, html_params
from wtforms.fields.core import _unset_value

from flask.ext.admin.babel import gettext

__all__ = ['FileUploadInput', 'FileUploadField', 'namefn_keep_filename']


# Widgets
class FileUploadInput(object):
    """
        Renders a file input chooser field.
    """
    template = ('<input %(text)s><input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        return HTMLString(self.template % {
            'text': html_params(type='text',
                                value=kwargs.get('value')),
            'file': html_params(type='file',
                                **kwargs)
        })


# Fields
class FileUploadField(fields.TextField):
    """
        Customizable file-upload field
    """
    widget = FileUploadInput()

    def __init__(self, label=None, validators=None,
                 path=None, namefn=None, endpoint='static', allowed_extensions=None,
                 **kwargs):
        if not path:
            raise ValueError('FileUploadField field requires target path.')

        self.path = path
        self.namefn = namefn or namefn_keep_filename
        self.endpoint = endpoint
        self.allowed_extensions = allowed_extensions
        self._should_delete = False

        super(FileUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        if not self.allowed_extensions:
            return True

        return ('.' in filename and
                filename.rsplit('.', 1)[1] in self.allowed_extensions)

    def pre_validate(self, form):
        if isinstance(self.data, FileStorage) and not self.is_file_allowed(self.data.filename):
            raise ValidationError(gettext('Invalid file extension'))

    def process(self, formdata, data=_unset_value):
        if formdata:
            marker = '_%s-delete' % self.name
            if marker in formdata:
                self._should_delete = True

        return super(FileUploadField, self).process(formdata, data)

    def populate_obj(self, obj, name):
        field = getattr(obj, name, None)
        if field:
            # If field should be deleted, clean it up
            if self._should_delete:
                self._delete_file(field)
                return

        if isinstance(self.data, FileStorage):
            if field:
                self._delete_file(field)

            filename = self.namefn(obj, self.data)
            self._save_file(self.data, filename)

            setattr(obj, name, filename)

    def _delete_file(self, filename):
        path = op.join(self.path, filename)
        os.remove(path)

    def _save_file(self, data, filename):
        data.save(op.join(self.path, filename))


# Helpers
def namefn_keep_filename(obj, file_data):
    return secure_filename(file_data.filename)
