from wtforms.widgets import html_params

from jinja2 import escape

from mongoengine.fields import GridFSProxy, ImageGridFsProxy

from flask_admin._backwards import Markup
from flask_admin.helpers import get_url
from . import helpers


class MongoFileInput(object):
    """
        Renders a file input chooser field.
    """
    template = ('<div>'
                ' <i class="icon-file"></i>%(name)s %(size)dk (%(content_type)s)'
                ' <input type="checkbox" name="%(marker)s">Delete</input>'
                '</div>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        placeholder = ''
        if field.data and isinstance(field.data, GridFSProxy):
            data = field.data

            placeholder = self.template % {
                'name': escape(data.name),
                'content_type': escape(data.content_type),
                'size': data.length // 1024,
                'marker': '_%s-delete' % field.name
            }

        return Markup('%s<input %s>' % (placeholder,
                      html_params(name=field.name,
                                  type='file',
                                  **kwargs)))


class MongoImageInput(object):
    """
        Renders a file input chooser field.
    """
    template = ('<div class="image-thumbnail">'
                ' <img src="%(thumb)s"/>'
                ' <input type="checkbox" name="%(marker)s">Delete</input>'
                '</div>')

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        placeholder = ''
        if field.data and isinstance(field.data, ImageGridFsProxy):
            args = helpers.make_thumb_args(field.data)
            placeholder = self.template % {
                'thumb': get_url('.api_file_view', **args),
                'marker': '_%s-delete' % field.name
            }

        return Markup('%s<input %s>' % (placeholder,
                      html_params(name=field.name,
                                  type='file',
                                  **kwargs)))
