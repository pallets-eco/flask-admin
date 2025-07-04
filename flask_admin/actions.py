import typing as t
from typing import Any

from flask import redirect
from flask import request

from flask_admin import tools
from flask_admin._compat import text_type
from flask_admin._types import T_RESPONSE
from flask_admin.helpers import flash_errors
from flask_admin.helpers import get_redirect_target


def action(name: str, text: str, confirmation: t.Optional[str] = None) -> t.Callable:
    """
    Use this decorator to expose actions that span more than one
    entity (model, file, etc)

    :param name:
        Action name
    :param text:
        Action text.
    :param confirmation:
        Confirmation text. If not provided, action will be executed
        unconditionally.
    """

    def wrap(f: t.Callable) -> t.Callable:
        f._action = (name, text, confirmation)  # type: ignore[attr-defined]
        return f

    return wrap


class ActionsMixin:
    """
    Actions mixin.

    In some cases, you might work with more than one "entity" (model, file, etc) in
    your admin view and will want to perform actions on a group of entities
    simultaneously.

    In this case, you can add this functionality by doing this:
    1. Add this mixin to your administrative view class
    2. Call `init_actions` in your class constructor
    3. Expose actions view
    4. Import `actions.html` library and add call library macros in your template
    """

    def __init__(self) -> None:
        """
        Default constructor.
        """
        self._actions: list[tuple[str, str]] = []
        self._actions_data: dict[str, tuple[Any, str, t.Optional[str]]] = {}

    def init_actions(self) -> None:
        """
        Initialize list of actions for the current administrative view.
        """
        self._actions: list[tuple[str, str]] = []  # type:ignore[no-redef]
        self._actions_data: dict[str, tuple[Any, str, t.Optional[str]]] = {}  # type:ignore[no-redef]

        for p in dir(self):
            attr = tools.get_dict_attr(self, p)

            if hasattr(attr, "_action"):
                name, text, desc = attr._action  # type: ignore[union-attr]

                self._actions.append((name, text))

                # TODO: Use namedtuple
                # Reason why we need getattr here - what's in attr is not
                # bound to the object.
                self._actions_data[name] = (getattr(self, p), text, desc)

    def is_action_allowed(self, name: str) -> bool:
        """
        Verify if action with `name` is allowed.

        :param name:
            Action name
        """
        return True

    def get_actions_list(self) -> tuple[list[t.Any], dict[t.Any, t.Any]]:
        """
        Return a list and a dictionary of allowed actions.
        """
        actions = []
        actions_confirmation = {}

        for act in self._actions:
            name, text = act

            if self.is_action_allowed(name):
                actions.append((name, text_type(text)))

                confirmation = self._actions_data[name][2]
                if confirmation:
                    actions_confirmation[name] = text_type(confirmation)

        return actions, actions_confirmation

    def handle_action(self, return_view: t.Optional[str] = None) -> T_RESPONSE:
        """
        Handle action request.

        :param return_view:
            Name of the view to return to after the request.
            If not provided, will return user to the return url in the form
            or the list view.
        """
        form = self.action_form()  # type: ignore[attr-defined]

        if self.validate_form(form):  # type: ignore[attr-defined]
            # using getlist instead of FieldList for backward compatibility
            ids = request.form.getlist("rowid")
            action = form.action.data

            handler = self._actions_data.get(action)

            if handler and self.is_action_allowed(action):
                response = handler[0](ids)

                if response is not None:
                    return response
        else:
            flash_errors(form, message="Failed to perform action. %(error)s")

        if return_view:
            url = self.get_url("." + return_view)  # type: ignore[attr-defined]
        else:
            url = get_redirect_target() or self.get_url(".index_view")  # type: ignore[attr-defined]

        return redirect(url)
