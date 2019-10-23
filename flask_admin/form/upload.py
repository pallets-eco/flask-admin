import os
import os.path as op

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from wtforms import ValidationError, fields
from wtforms.widgets import html_params

try:
    from wtforms.fields.core import _unset_value as unset_value
except ImportError:
    from wtforms.utils import unset_value

from flask_admin.babel import gettext
from flask_admin.helpers import get_url

from flask_admin._backwards import Markup
from flask_admin._compat import string_types, urljoin


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

        if field.errors:
            template = self.empty_template

        if field.data and isinstance(field.data, FileStorage):
            value = field.data.filename
        else:
            value = field.data or ''

        return Markup(template % {
            'text': html_params(type='text',
                                readonly='readonly',
                                value=value,
                                name=field.name),
            'file': html_params(type='file',
                                value=value,
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
                     ' <input %(text)s>'
                     '</div>'
                     '<input %(file)s>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        args = {
            'text': html_params(type='hidden',
                                value=field.data,
                                name=field.name),
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

        return Markup(template % args)

    def get_url(self, field):
        if field.thumbnail_size:
            filename = field.thumbnail_fn(field.data)
        else:
            filename = field.data

        if field.url_relative_path:
            filename = urljoin(field.url_relative_path, filename)

        return get_url(field.endpoint, filename=filename)


# Fields
class FileUploadField(fields.StringField):
    """
        Customizable file-upload field.

        Saves file to configured path, handles updates and deletions. Inherits from `StringField`,
        resulting filename will be stored as string.
    """
    widget = FileUploadInput()

    def __init__(self, label=None, validators=None,
                 base_path=None, relative_path=None,
                 namegen=None, allowed_extensions=None,
                 permission=0o666, allow_overwrite=True,
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
            :param allow_overwrite:
                Whether to overwrite existing files in upload directory. Defaults to `True`.

            .. versionadded:: 1.1.1
                The `allow_overwrite` parameter was added.
        """
        self.base_path = base_path
        self.relative_path = relative_path

        self.namegen = namegen or namegen_filename
        self.allowed_extensions = allowed_extensions
        self.permission = permission
        self._allow_overwrite = allow_overwrite

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
                filename.rsplit('.', 1)[1].lower() in
                map(lambda x: x.lower(), self.allowed_extensions))

    def _is_uploaded_file(self, data):
        return (data and isinstance(data, FileStorage) and data.filename)

    def pre_validate(self, form):
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(self.data.filename):
            raise ValidationError(gettext('Invalid file extension'))

        # Handle overwriting existing content
        if not self._is_uploaded_file(self.data):
            return

        if not self._allow_overwrite and os.path.exists(self._get_path(self.data.filename)):
            raise ValidationError(gettext('File "%s" already exists.' % self.data.filename))

    def process(self, formdata, data=unset_value):
        if formdata:
            marker = '_%s-delete' % self.name
            if marker in formdata:
                self._should_delete = True

        return super(FileUploadField, self).process(formdata, data)

    def process_formdata(self, valuelist):
        if self._should_delete:
            self.data = None
        elif valuelist:
            for data in valuelist:
                if self._is_uploaded_file(data):
                    self.data = data
                    break

    def populate_obj(self, obj, name):
        field = getattr(obj, name, None)
        if field:
            # If field should be deleted, clean it up
            if self._should_delete:
                self._delete_file(field)
                setattr(obj, name, None)
                return

        if self._is_uploaded_file(self.data):
            if field:
                self._delete_file(field)

            filename = self.generate_name(obj, self.data)
            filename = self._save_file(self.data, filename)
            # update filename of FileStorage to our validated name
            self.data.filename = filename

            setattr(obj, name, filename)

    def generate_name(self, obj, file_data):
        filename = self.namegen(obj, file_data)

        if not self.relative_path:
            return filename

        return urljoin(self.relative_path, filename)

    def _get_path(self, filename):
        if not self.base_path:
            raise ValueError('FileUploadField field requires base_path to be set.')

        if callable(self.base_path):
            return op.join(self.base_path(), filename)
        return op.join(self.base_path, filename)

    def _delete_file(self, filename):
        path = self._get_path(filename)

        if op.exists(path):
            os.remove(path)

    def _save_file(self, data, filename):
        path = self._get_path(filename)
        if not op.exists(op.dirname(path)):
            os.makedirs(os.path.dirname(path), self.permission | 0o111)

        if (self._allow_overwrite is False) and os.path.exists(path):
            raise ValueError(gettext('File "%s" already exists.' % path))

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
                 permission=0o666,
                 url_relative_path=None, endpoint='static',
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
                List of allowed extensions. If not provided, then gif, jpg, jpeg, png and tiff will be allowed.
            :param max_size:
                Tuple of (width, height, force) or None. If provided, Flask-Admin will
                resize image to the desired size.

                Width and height is in pixels. If `force` is set to `True`, will try to fit image into dimensions and
                keep aspect ratio, otherwise will just resize to target size.
            :param thumbgen:
                Thumbnail filename generation function. All thumbnails will be saved as JPEG files,
                so there's no need to keep original file extension.

                For example::

                    import os.path as op

                    def thumb_name(filename):
                        name, _ = op.splitext(filename)
                        return secure_filename('%s-thumb.jpg' % name)

                    class MyForm(BaseForm):
                        upload = ImageUploadField('File', thumbgen=thumb_name)

            :param thumbnail_size:
                Tuple or (width, height, force) values. If not provided, thumbnail won't be created.

                Width and height is in pixels. If `force` is set to `True`, will try to fit image into dimensions and
                keep aspect ratio, otherwise will just resize to target size.
            :param url_relative_path:
                Relative path from the root of the static directory URL. Only gets used when generating
                preview image URLs.

                For example, your model might store just file names (`relative_path` set to `None`), but
                `base_path` is pointing to subdirectory.
            :param endpoint:
                Static endpoint for images. Used by widget to display previews. Defaults to 'static'.
        """
        # Check if PIL is installed
        if Image is None:
            raise ImportError('PIL library was not found')

        self.max_size = max_size
        self.thumbnail_fn = thumbgen or thumbgen_filename
        self.thumbnail_size = thumbnail_size
        self.endpoint = endpoint
        self.image = None
        self.url_relative_path = url_relative_path

        if not allowed_extensions:
            allowed_extensions = ('gif', 'jpg', 'jpeg', 'png', 'tiff')

        super(ImageUploadField, self).__init__(label, validators,
                                               base_path=base_path,
                                               relative_path=relative_path,
                                               namegen=namegen,
                                               allowed_extensions=allowed_extensions,
                                               permission=permission,
                                               **kwargs)

    def pre_validate(self, form):
        super(ImageUploadField, self).pre_validate(form)

        if self._is_uploaded_file(self.data):
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
        path = self._get_path(filename)

        if not op.exists(op.dirname(path)):
            os.makedirs(os.path.dirname(path), self.permission | 0o111)

        # Figure out format
        filename, format = self._get_save_format(filename, self.image)

        if self.image and (self.image.format != format or self.max_size):
            if self.max_size:
                image = self._resize(self.image, self.max_size)
            else:
                image = self.image

            self._save_image(image, self._get_path(filename), format)
        else:
            data.seek(0)
            data.save(self._get_path(filename))

        self._save_thumbnail(data, filename, format)

        return filename

    def _save_thumbnail(self, data, filename, format):
        if self.image and self.thumbnail_size:
            path = self._get_path(self.thumbnail_fn(filename))

            self._save_image(self._resize(self.image, self.thumbnail_size),
                             path,
                             format)

    def _resize(self, image, size):
        (width, height, force) = size

        if image.size[0] > width or image.size[1] > height:
            if force:
                return ImageOps.fit(self.image, (width, height), Image.ANTIALIAS)
            else:
                thumb = self.image.copy()
                thumb.thumbnail((width, height), Image.ANTIALIAS)
                return thumb

        return image

    def _save_image(self, image, path, format='JPEG'):
        # New Pillow versions require RGB format for JPEGs
        if format == 'JPEG' and image.mode != 'RGB':
            image = image.convert('RGB')
        elif image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        with open(path, 'wb') as fp:
            image.save(fp, format)

    def _get_save_format(self, filename, image):
        if image.format not in self.keep_image_formats:
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
    return '%s_thumb%s' % (name, ext)
