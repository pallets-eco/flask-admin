import os
import os.path as op

from flask import url_for

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from wtforms import ValidationError, fields
from wtforms.widgets import HTMLString, html_params
from wtforms.fields.core import _unset_value

from flask.ext.admin.babel import gettext

from flask.ext.admin._compat import string_types, urljoin


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

        You can customize `empty_template` and `data_template` members to customize
        look and feel.
    """
    empty_template = ('<input %(file)s>')

    data_template = ('<div>'
                     ' <input %(text)s>'
                     ' <input type="checkbox" name="%(marker)s">Delete</input>'
                     '</div>'
                     '<input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        template = self.data_template if field.data else self.empty_template

        return HTMLString(template % {
            'text': html_params(type='text',
                                readonly='readonly',
                                value=field.data),
            'file': html_params(type='file',
                                **kwargs),
            'marker': '_%s-delete' % field.name
        })


class ImageUploadInput(object):
    """
        Renders a image input chooser field.

        You can customize `empty_template` and `data_template` members to customize
        look and feel.
    """
    empty_template = ('<input %(file)s>')

    data_template = ('<div class="image-thumbnail">'
                     ' <img %(image)s>'
                     ' <input type="checkbox" name="%(marker)s">Delete</input>'
                     '</div>'
                     '<input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        args = {
            'file': html_params(type='file',
                                **kwargs),
            'marker': '_%s-delete' % field.name
        }

        if field.data and isinstance(field.data, string_types):
            url = self.get_url(field)
            args['image'] = html_params(src=url)

            template = self.data_template
        else:
            template = self.empty_template

        return HTMLString(template % args)

    def get_url(self, field):
        if field.thumbnail_size:
            return url_for(field.endpoint, filename=field.thumbnail_fn(field.data))

        return url_for(field.endpoint, filename=field.data)


# Fields
class FileUploadField(fields.TextField):
    """
        Customizable file-upload field.

        Saves file to configured path, handles updates and deletions. Inherits from `TextField`,
        resulting filename will be stored as string.
    """
    widget = FileUploadInput()

    def __init__(self, label=None, validators=None,
                 base_path=None, relative_path=None,
                 namegen=None, allowed_extensions=None,
                 **kwargs):
        """
            Constructor.

            :param label:
                Display label
            :param validators:
                Validators
            :param base_path:
                Absolute path to the directory which will store files
            :param relative_path:
                Relative path from the directory. Will be prepended to the file name for uploaded files.
                Flask-Admin uses `urlparse.urljoin` to generate resulting filename, so make sure you have
                trailing slash.
            :param namegen:
                Function that will generate filename from the model and uploaded file object.
                Please note, that model is "dirty" model object, before it was committed to database.

                For example::

                    import os.path as op

                    def prefix_name(obj, file_data):
                        parts = op.splitext(file_data.filename)
                        return secure_filename('file-%s%s' % parts)

                    class MyForm(BaseForm):
                        upload = FileUploadField('File', namegen=prefix_name)

            :param allowed_extensions:
                List of allowed extensions. If not provided, will allow any file.
        """
        self.base_path = base_path
        self.relative_path = relative_path

        self.namegen = namegen or namegen_filename
        self.allowed_extensions = allowed_extensions
        self._should_delete = False

        super(FileUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        """
            Check if file extension is allowed.

            :param filename:
                File name to check
        """
        if not self.allowed_extensions:
            return True

        return ('.' in filename and
                filename.rsplit('.', 1)[1] in self.allowed_extensions)

    def pre_validate(self, form):
        if (self.data and
                isinstance(self.data, FileStorage) and
                not self.is_file_allowed(self.data.filename)):
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
                setattr(obj, name, None)
                return

        if self.data and isinstance(self.data, FileStorage):
            if field:
                self._delete_file(field)

            filename = self.generate_name(obj, self.data)
            filename = self._save_file(self.data, filename)

            setattr(obj, name, filename)

    def generate_name(self, obj, file_data):
        filename = self.namegen(obj, file_data)

        if not self.relative_path:
            return filename

        return urljoin(self.relative_path, filename)

    def _get_path(self, filename):
        if not self.base_path:
            raise ValueError('FileUploadField field requires base_path to be set.')

        return op.join(self.base_path, filename)

    def _delete_file(self, filename):
        path = self._get_path(filename)

        if op.exists(path):
            os.remove(path)

    def _save_file(self, data, filename):
        path = self._get_path(filename)
        data.save(path)

        return filename


class ImageUploadField(FileUploadField):
    """
        Image upload field.

        Does image validation, thumbnail generation, updating and deleting images.

        Requires PIL (or Pillow) to be installed.
    """
    widget = ImageUploadInput()

    keep_image_formats = ('PNG',)
    """
        If field detects that uploaded image is not in this list, it will save image
        as PNG.
    """

    def __init__(self, label=None, validators=None,
                 base_path=None, relative_path=None,
                 namegen=None, allowed_extensions=None,
                 max_size=None,
                 thumbgen=None, thumbnail_size=None,
                 endpoint='static',
                 **kwargs):
        """
            Constructor.

            :param label:
                Display label
            :param validators:
                Validators
            :param base_path:
                Absolute path to the directory which will store files
            :param relative_path:
                Relative path from the directory. Will be prepended to the file name for uploaded files.
                Flask-Admin uses `urlparse.urljoin` to generate resulting filename, so make sure you have
                trailing slash.
            :param namegen:
                Function that will generate filename from the model and uploaded file object.
                Please note, that model is "dirty" model object, before it was committed to database.

                For example::

                    import os.path as op

                    def prefix_name(obj, file_data):
                        parts = op.splitext(file_data.filename)
                        return secure_filename('file-%s%s' % parts)

                    class MyForm(BaseForm):
                        upload = FileUploadField('File', namegen=prefix_name)

            :param allowed_extensions:
                List of allowed extensions. If not provided, will allow any file.
            :param max_size:
                Tuple of (width, height, force) or None. If provided, Flask-Admin will
                resize image to the desired size.
            :param thumbgen:
                Thumbnail filename generation function. All thumbnails will be saved as JPEG files,
                so there's no need to keep original file extension.

                For example::

                    import os.path as op

                    def thumb_name(filename):
                        name, _ = op.splitext(filename)
                        return secure_filename('%s-thumb.jpg' % name)

                    class MyForm(BaseForm):
                        upload = ImageUploadField('File', thumbgen=prefix_name)

            :param thumbnail_size:
                Tuple or (width, height, force) values. If not provided, thumbnail won't be created.

                Width and height is in pixels. If `force` is set to `True`, will try to fit image into dimensions and
                keep aspect ratio, otherwise will just resize to target size.
            :param endpoint:
                Static endpoint for images. Used by widget to display previews. Defaults to 'static'.
        """
        # Check if PIL is installed
        if Image is None:
            raise Exception('PIL library was not found')

        self.max_size = max_size
        self.thumbnail_fn = thumbgen or thumbgen_filename
        self.thumbnail_size = thumbnail_size
        self.endpoint = endpoint
        self.image = None

        if not allowed_extensions:
            allowed_extensions = ('gif', 'jpg', 'jpeg', 'png', 'tiff')

        super(ImageUploadField, self).__init__(label, validators,
                                               base_path=base_path,
                                               relative_path=relative_path,
                                               namegen=namegen,
                                               allowed_extensions=allowed_extensions,
                                               **kwargs)

    def pre_validate(self, form):
        super(ImageUploadField, self).pre_validate(form)

        if self.data and isinstance(self.data, FileStorage):
            try:
                self.image = Image.open(self.data)
            except Exception as e:
                raise ValidationError('Invalid image: %s' % e)

    # Deletion
    def _delete_file(self, filename):
        super(ImageUploadField, self)._delete_file(filename)

        self._delete_thumbnail(filename)

    def _delete_thumbnail(self, filename):
        path = self._get_path(self.thumbnail_fn(filename))

        if op.exists(path):
            os.remove(path)

    # Saving
    def _save_file(self, data, filename):
        if self.image and self.max_size:
            filename, format = self._get_save_format(filename, self.image)

            self._save_image(self._resize(self.image, self.max_size),
                             self._get_path(filename),
                             format)
        else:
            data.save(self._get_path(filename))

        self._save_thumbnail(data, filename)

        return filename

    def _save_thumbnail(self, data, filename):
        if self.image and self.thumbnail_size:
            path = self._get_path(self.thumbnail_fn(filename))

            self._save_image(self._resize(self.image, self.thumbnail_size),
                             path)

    def _resize(self, image, size):
        (width, height, force) = size

        if image.size[0] > width or image.size[1] > height:
            if force:
                return ImageOps.fit(self.image, (width, height), Image.ANTIALIAS)
            else:
                return self.image.copy().thumbnail((width, height), Image.ANTIALIAS)

        return image

    def _save_image(self, image, path, format='JPEG'):
        with open(path, 'wb') as fp:
            image.save(fp, format)

    def _get_save_format(self, filename, image):
        if not image.format in self.keep_image_formats:
            name, ext = op.splitext(filename)
            filename = '%s.jpg' % name
            return filename, 'JPEG'

        return filename, image.format


# Helpers
def namegen_filename(obj, file_data):
    """
        Generate secure filename for uploaded file.
    """
    return secure_filename(file_data.filename)


def thumbgen_filename(filename):
    """
        Generate thumbnail name from filename.
    """
    name, ext = op.splitext(filename)
    return '%s_thumb.jpg' % name
