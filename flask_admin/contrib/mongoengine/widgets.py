from wtforms.widgets import HTMLString, html_params

from jinja2 import escape


class MongoFileInput(object):
    """
        Renders a file input chooser field.
    """
    template = '<div><i class="icon-file"></i>%(name)s %(length)dk (%(content_type)s)</div>'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)

        placeholder = ''
        if field.data:
            placeholder = self.template % dict(
                    name=escape(field.data.filename),
                    content_type=escape(field.data.content_type),
                    length=field.data.length // 1024)

        return HTMLString('%s<input %s>' % (placeholder,
                                            html_params(name=field.name,
                                                        type='file',
                                                        **kwargs)))
