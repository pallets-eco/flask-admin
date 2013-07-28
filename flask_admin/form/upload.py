import os
import os.path as op
import logging

from flask import url_for

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from jinja2 import escape

from wtforms import ValidationError, fields
from wtforms.widgets import HTMLString, html_params
from wtforms.fields.core import _unset_value

from flask.ext.admin.babel import gettext

from flask.ext.admin._compat import string_types


try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None


__all__ = ['FileUploadInput', 'FileUploadField',
           'ImageUploadInput', 'ImageUploadField',
           'namegen_filename', 'thumbgen_filename']


# Widgets
class FileUploadInput(object):
    """
        Renders a file input chooser field.
    """
    empty_template = ('<input %(file)s>')

    data_template = ('<div>'
                     ' <input %(text)s>'
                     ' <input type="checkbox" name="%(marker)s">Delete</input>'
                     '</div>'
                     '<input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        template = self.data_template if field.data else self.empty_template

        return HTMLString(template % {
            'text': html_params(type='text',
                                readonly='readonly',
                                value=kwargs.get('value')),
            'file': html_params(type='file',
                                **kwargs),
            'marker': '_%s-delete' % field.name
        })


class ImageUploadInput(object):
    """
        Renders a file input chooser field.
    """
    empty_template = ('<input %(file)s>')

    data_template = ('<div>'
                     ' <img %(image)s>'
                     ' <input type="checkbox" name="%(marker)s">Delete</input>'
                     '</div>'
                     '<input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        args = {
            'file': html_params(type='file',
                                **kwargs),
            'marker': '_%s-delete' % field.name
        }

        value = kwargs.get('value')
        if value and isinstance(value, string_types):
            args['image'] = html_params(src=url_for(field.endpoint,
                                                    filename=field.thumnbnail_fn(value)))

            template = self.data_template
        else:
            template = self.empty_template

        return HTMLString(template % args)


# Fields
class FileUploadField(fields.TextField):
    """
        Customizable file-upload field
    """
    widget = FileUploadInput()

    def __init__(self, label=None, validators=None,
                 path=None, namegen=None, allowed_extensions=None,
                 **kwargs):
        if not path:
            raise ValueError('FileUploadField field requires target path.')

        self.path = path
        self.namegen = namegen or namegen_filename
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

            filename = self.namegen(obj, self.data)
            self._save_file(self.data, filename)

            setattr(obj, name, filename)

    def _delete_file(self, filename):
        path = op.join(self.path, filename)

        if op.exists(path):
            os.remove(path)

    def _save_file(self, data, filename):
        data.save(op.join(self.path, filename))


class ImageUploadField(FileUploadField):
    widget = ImageUploadInput()

    def __init__(self, label=None, validators=None,
                 path=None, namegen=None, allowed_extensions=None,
                 thumbgen=None, thumbnail_size=None, endpoint='static',
                 **kwargs):
        # Check if PIL is installed
        if Image is None:
            raise Exception('PIL library was not found')

        self.thumbnail_fn = thumbgen or thumbgen_filename
        self.thumbnail_size = thumbnail_size
        self.endpoint = endpoint
        self.image = None

        if not allowed_extensions:
            allowed_extensions = ('gif', 'jpg', 'jpeg', 'png')

        super(ImageUploadField, self).__init__(label, validators,
                                               path=path,
                                               namegen=namegen,
                                               allowed_extensions=allowed_extensions,
                                               **kwargs)

    def pre_validate(self, form):
        super(ImageUploadField, self).pre_validate(form)

        if isinstance(self.data, FileStorage):
            try:
                self.image = Image.open(self.data)
            except Exception as e:
                raise ValidationError('Invalid image: %s' % e)

    # Deletion
    def _delete_file(self, filename):
        super(ImageUploadField, self)._delete_file(filename)

        self._delete_thumbnail(filename)

    def _delete_thumbnail(self, filename):
        path = op.join(self.path, self.thumbnail_fn(filename))

        if op.exists(path):
            os.remove(path)

    # Saving
    def _save_file(self, data, filename):
        data.save(op.join(self.path, filename))

        self._save_thumbnail(data, filename)

    def _save_thumbnail(self, data, filename):
        if self.image and self.thumbnail_size:
            thumb = self.image

            (width, height, force) = self.thumbnail_size

            if self.image.size[0] > width or self.image.size[1] > height:
                if force:
                    thumb = ImageOps.fit(self.image, (width, height), Image.ANTIALIAS)
                else:
                    thumb = self.image.copy().thumbnail((width, height), Image.ANTIALIAS)

            path = op.join(self.path, self.thumbnail_fn(filename))
            with file(path, 'wb') as fp:
                thumb.save(fp, 'JPEG')


# Helpers
def namegen_filename(obj, file_data):
    return secure_filename(file_data.filename)


def thumbgen_filename(filename):
    name, ext = op.splitext(filename)
    return '%s_thumb.jpg' % name
