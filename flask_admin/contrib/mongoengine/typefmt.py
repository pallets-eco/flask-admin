from flask import url_for
from jinja2 import Markup, escape

from mongoengine.base import BaseList
from mongoengine.fields import GridFSProxy

from flask.ext.admin.model.typefmt import BASE_FORMATTERS, list_formatter


def gridfs_formatter(view, model, name, value):
    return Markup(
        '<a href="%s" target="_blank"><i class="icon-file"></i>%s</a> %dk (%s)' % (
            url_for('.api_file_view', id=model.id, name=name),
            escape(value.filename),
            value.length // 1024,
            escape(value.content_type))
    )


DEFAULT_FORMATTERS = BASE_FORMATTERS.copy()
DEFAULT_FORMATTERS.update({
    BaseList: list_formatter,
    GridFSProxy: gridfs_formatter
})
