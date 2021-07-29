from markupsafe import Markup, escape

from mongoengine.base import BaseList
from mongoengine.fields import GridFSProxy, ImageGridFsProxy

from flask_admin.model.typefmt import BASE_FORMATTERS, list_formatter

from . import helpers


def grid_formatter(view, value):
    if not value.grid_id:
        return ''

    args = helpers.make_gridfs_args(value)

    return Markup(
        ('<a href="%(url)s" target="_blank">' +
            '<i class="icon-file"></i>%(name)s' +
         '</a> %(size)dk (%(content_type)s)') %
        {
            'url': view.get_url('.api_file_view', **args),
            'name': escape(value.name),
            'size': value.length // 1024,
            'content_type': escape(value.content_type)
        })


def grid_image_formatter(view, value):
    if not value.grid_id:
        return ''

    return Markup(
        ('<div class="image-thumbnail">' +
            '<a href="%(url)s" target="_blank"><img src="%(thumb)s"/></a>' +
         '</div>') %
        {
            'url': view.get_url('.api_file_view', **helpers.make_gridfs_args(value)),
            'thumb': view.get_url('.api_file_view', **helpers.make_thumb_args(value)),
        })


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS.update({
    BaseList: list_formatter,
    GridFSProxy: grid_formatter,
    ImageGridFsProxy: grid_image_formatter
})
