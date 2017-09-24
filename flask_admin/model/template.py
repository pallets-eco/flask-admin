from jinja2 import contextfunction

from flask_admin._compat import string_types, reduce
from flask_admin.babel import gettext


class BaseListRowAction(object):
    def __init__(self, title=None):
        self.title = title

    def render(self, context, row_id, row):
        raise NotImplementedError()

    @contextfunction
    def render_ctx(self, context, row_id, row):
        return self.render(context, row_id, row)

    def _resolve_symbol(self, context, symbol):
        if '.' in symbol:
            parts = symbol.split('.')
            m = context.resolve(parts[0])
            return reduce(getattr, parts[1:], m)
        else:
            return context.resolve(symbol)


class LinkRowAction(BaseListRowAction):
    def __init__(self, icon_class, url, title=None):
        super(LinkRowAction, self).__init__(title=title)

        self.url = url
        self.icon_class = icon_class

    def render(self, context, row_id, row):
        m = self._resolve_symbol(context, 'row_actions.link')

        if isinstance(self.url, string_types):
            url = self.url.format(row_id=row_id)
        else:
            url = self.url(self, row_id, row)

        return m(self, url)


class EndpointLinkRowAction(BaseListRowAction):
    def __init__(self, icon_class, endpoint, title=None, id_arg='id', url_args=None):
        super(EndpointLinkRowAction, self).__init__(title=title)

        self.icon_class = icon_class
        self.endpoint = endpoint
        self.id_arg = id_arg
        self.url_args = url_args

    def render(self, context, row_id, row):
        m = self._resolve_symbol(context, 'row_actions.link')
        get_url = self._resolve_symbol(context, 'get_url')

        kwargs = dict(self.url_args) if self.url_args else {}
        kwargs[self.id_arg] = row_id

        url = get_url(self.endpoint, **kwargs)

        return m(self, url)


class TemplateLinkRowAction(BaseListRowAction):
    def __init__(self, template_name, title=None):
        super(TemplateLinkRowAction, self).__init__(title=title)

        self.template_name = template_name

    def render(self, context, row_id, row):
        m = self._resolve_symbol(context, self.template_name)
        return m(self, row_id, row)


class ViewRowAction(TemplateLinkRowAction):
    def __init__(self):
        super(ViewRowAction, self).__init__(
            'row_actions.view_row',
            gettext('View Record'))


class ViewPopupRowAction(TemplateLinkRowAction):
    def __init__(self):
        super(ViewPopupRowAction, self).__init__(
            'row_actions.view_row_popup',
            gettext('View Record'))


class EditRowAction(TemplateLinkRowAction):
    def __init__(self):
        super(EditRowAction, self).__init__(
            'row_actions.edit_row',
            gettext('Edit Record'))


class EditPopupRowAction(TemplateLinkRowAction):
    def __init__(self):
        super(EditPopupRowAction, self).__init__(
            'row_actions.edit_row_popup',
            gettext('Edit Record'))


class DeleteRowAction(TemplateLinkRowAction):
    def __init__(self):
        super(DeleteRowAction, self).__init__(
            'row_actions.delete_row',
            gettext('Delete Record'))


# Macro helper
def macro(name):
    '''
        Jinja2 macro list column formatter.

        :param name:
            Macro name in the current template
    '''
    def inner(view, context, model, column):
        m = context.resolve(name)

        if not m:
            return m

        return m(model=model, column=column)

    return inner
