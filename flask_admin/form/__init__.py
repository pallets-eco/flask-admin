import typing as t
from os import urandom

from flask import current_app
from flask import session
from wtforms import Field
from wtforms import form
from wtforms.csrf.session import SessionCSRF
from wtforms.fields.core import UnboundField

from flask_admin._compat import text_type
from flask_admin.babel import Translations

from .fields import *  # noqa: F403,F401
from .upload import *  # noqa: F403,F401
from .widgets import *  # noqa: F403,F401


class BaseForm(form.Form):
    class Meta:
        _translations = Translations()

        def get_translations(self, form: "BaseForm") -> Translations:
            return self._translations

    def __init__(
        self,
        formdata: t.Optional[dict] = None,
        obj: t.Any = None,
        prefix: str = "",
        **kwargs: t.Any,
    ) -> None:
        self._obj = obj

        super().__init__(
            formdata=formdata,  # type: ignore[arg-type]
            obj=obj,
            prefix=prefix,
            **kwargs,
        )


class FormOpts:
    __slots__ = ["widget_args", "form_rules"]

    def __init__(
        self, widget_args: t.Optional[dict] = None, form_rules: t.Any = None
    ) -> None:
        self.widget_args = widget_args or {}
        self.form_rules = form_rules


def recreate_field(unbound: t.Union[UnboundField, Field]) -> t.Any:
    """
    Create new instance of the unbound field, resetting wtforms creation counter.

    :param unbound:
        UnboundField instance
    """
    if not isinstance(unbound, UnboundField):
        raise ValueError(
            f"recreate_field expects UnboundField instance, {type(unbound)} was passed."
        )

    return unbound.field_class(*unbound.args, **unbound.kwargs)


class SecureForm(BaseForm):
    """
    BaseForm with CSRF token generation and validation support.

    Requires WTForms 2+
    """

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        _csrf_secret = urandom(24)

        @property
        def csrf_secret(self) -> t.Union[bytes, str, None]:
            secret = current_app.secret_key or self._csrf_secret
            if isinstance(secret, text_type):
                secret = secret.encode("utf-8")
            return secret

        @property
        def csrf_context(self) -> t.Any:
            return session
