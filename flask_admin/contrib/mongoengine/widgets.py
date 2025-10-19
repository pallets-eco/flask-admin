from markupsafe import escape
from markupsafe import Markup
from mongoengine.fields import GridFSProxy
from mongoengine.fields import ImageGridFsProxy
from wtforms.widgets import html_params

from flask_admin.helpers import get_url

from . import helpers


class MongoFileInput:
    """
    Renders a file input chooser field.
    """

    template = (
        "<div>"
        ' <i class="icon-file"></i>%(name)s %(size)dk (%(content_type)s)'
        ' <input type="checkbox" name="%(marker)s">Delete</input>'
        "</div>"
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)

        placeholder = ""
        if field.data and isinstance(field.data, GridFSProxy):
            data = field.data

            placeholder = self.template % {
                "name": escape(data.name),
                "content_type": escape(data.content_type),
                "size": data.length // 1024,
                "marker": f"_{field.name}-delete",
            }

        params = html_params(name=field.name, type="file", **kwargs)
        return Markup(f"{placeholder}<input {params}>")


class MongoImageInput:
    """
    Renders a file input chooser field.
    """

    template = (
        '<div class="image-thumbnail">'
        ' <img src="%(thumb)s"/>'
        ' <input type="checkbox" name="%(marker)s">Delete</input>'
        "</div>"
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        placeholder = ""
        if field.data and isinstance(field.data, ImageGridFsProxy):
            args = helpers.make_thumb_args(field.data)
            placeholder = self.template % {
                "thumb": get_url(".api_file_view", **args),
                "marker": f"_{field.name}-delete",
            }

        params = html_params(name=field.name, type="file", **kwargs)
        return Markup(f"{placeholder}<input {params}>")
