import typing as t
from functools import reduce

from jinja2 import pass_context
from jinja2.runtime import Context

from flask_admin._compat import string_types
from flask_admin._types import T_COLUMN
from flask_admin._types import T_MODEL_VIEW
from flask_admin.babel import gettext


class BaseListRowAction:
    def __init__(self, title: t.Optional[str] = None) -> None:
        self.title = title

    def render(self, context: Context, row_id: str, row: t.Any) -> t.Any:
        raise NotImplementedError()

    @pass_context
    def render_ctx(self, context: Context, row_id: str, row: t.Any) -> t.Any:
        return self.render(context, row_id, row)

    def _resolve_symbol(self, context: Context, symbol: str) -> t.Any:
        if "." in symbol:
            parts = symbol.split(".")
            m = context.resolve(parts[0])
            return reduce(getattr, parts[1:], m)
        else:
            return context.resolve(symbol)


class LinkRowAction(BaseListRowAction):
    def __init__(
        self, icon_class: str, url: str, title: t.Optional[str] = None
    ) -> None:
        super().__init__(title=title)

        self.url = url
        self.icon_class = icon_class

    def render(self, context: Context, row_id: str, row: t.Any) -> t.Any:
        m = self._resolve_symbol(context, "row_actions.link")

        if isinstance(self.url, string_types):
            url = self.url.format(row_id=row_id)
        else:
            url = self.url(self, row_id, row)

        return m(self, url)


class EndpointLinkRowAction(BaseListRowAction):
    def __init__(
        self,
        icon_class: str,
        endpoint: str,
        title: t.Optional[str] = None,
        id_arg: str = "id",
        url_args: t.Optional[dict[str, t.Any]] = None,
    ) -> None:
        super().__init__(title=title)

        self.icon_class = icon_class
        self.endpoint = endpoint
        self.id_arg = id_arg
        self.url_args = url_args

    def render(self, context: Context, row_id: str, row: t.Any) -> t.Any:
        m = self._resolve_symbol(context, "row_actions.link")
        get_url = self._resolve_symbol(context, "get_url")

        kwargs = dict(self.url_args) if self.url_args else {}
        kwargs[self.id_arg] = row_id

        url = get_url(self.endpoint, **kwargs)

        return m(self, url)


class TemplateLinkRowAction(BaseListRowAction):
    def __init__(self, template_name: str, title: t.Optional[str] = None) -> None:
        super().__init__(title=title)

        self.template_name = template_name

    def render(self, context: Context, row_id: str, row: t.Any) -> t.Any:
        m = self._resolve_symbol(context, self.template_name)
        return m(self, row_id, row)


class ViewRowAction(TemplateLinkRowAction):
    def __init__(self) -> None:
        super().__init__("row_actions.view_row", gettext("View Record"))


class ViewPopupRowAction(TemplateLinkRowAction):
    def __init__(self) -> None:
        super().__init__("row_actions.view_row_popup", gettext("View Record"))


class EditRowAction(TemplateLinkRowAction):
    def __init__(self) -> None:
        super().__init__("row_actions.edit_row", gettext("Edit Record"))


class EditPopupRowAction(TemplateLinkRowAction):
    def __init__(self) -> None:
        super().__init__("row_actions.edit_row_popup", gettext("Edit Record"))


class DeleteRowAction(TemplateLinkRowAction):
    def __init__(self) -> None:
        super().__init__("row_actions.delete_row", gettext("Delete Record"))


# Macro helper
def macro(name: str) -> t.Callable[[t.Any, Context, T_MODEL_VIEW, T_COLUMN], t.Any]:
    """
    Jinja2 macro list column formatter.

    :param name:
        Macro name in the current template
    """

    def inner(
        view: t.Any, context: Context, model: T_MODEL_VIEW, column: T_COLUMN
    ) -> t.Any:
        m = context.resolve(name)

        if not m:
            return m

        return m(model=model, column=column)

    return inner
