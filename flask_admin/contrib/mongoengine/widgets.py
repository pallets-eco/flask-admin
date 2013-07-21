from wtforms.widgets import HTMLString, html_params

from jinja2 import escape
from flask import url_for

from . import helpers


class MongoFileInput(object):
    """
        Renders a file input chooser field.
    """
    template = '<div><i class="icon-file"></i>%(name)s %(size)dk (%(content_type)s)</div>'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        placeholder = ''
        if field.data:
            data = field.data

            placeholder = self.template % {
                'name': escape(data.name),
                'content_type': escape(data.content_type),
                'size': data.length // 1024
            }

        return HTMLString('%s<input %s>' % (placeholder,
                                            html_params(name=field.name,
                                                        type='file',
                                                        **kwargs)))


class MongoImageInput(object):
    """
        Renders a file input chooser field.
    """
    template = '<div class="image-thumbnail"><img src="%(thumb)s"/></div>'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        placeholder = ''
        if field.data:
            args = helpers.make_thumb_args(field.data)
            placeholder = self.template % {
                'thumb': url_for('.api_file_view', **args)
            }

        return HTMLString('%s<input %s>' % (placeholder,
                                            html_params(name=field.name,
                                                        type='file',
                                                        **kwargs)))
