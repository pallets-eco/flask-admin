from flask import request, redirect


from flask_admin import tools
from flask_admin._compat import text_type
from flask_admin.helpers import get_redirect_target


def action(name, text, confirmation=None):
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
    def wrap(f):
        f._action = (name, text, confirmation)
        return f

    return wrap


class ActionsMixin(object):
    """
        Actions mixin.

        In some cases, you might work with more than one "entity" (model, file, etc) in
        your admin view and will want to perform actions on a group of entities simultaneously.

        In this case, you can add this functionality by doing this:
        1. Add this mixin to your administrative view class
        2. Call `init_actions` in your class constructor
        3. Expose actions view
        4. Import `actions.html` library and add call library macros in your template
    """

    def __init__(self):
        """
            Default constructor.
        """
        self._actions = []
        self._actions_data = {}

    def init_actions(self):
        """
            Initialize list of actions for the current administrative view.
        """
        self._actions = []
        self._actions_data = {}

        for p in dir(self):
            attr = tools.get_dict_attr(self, p)

            if hasattr(attr, '_action'):
                name, text, desc = attr._action

                self._actions.append((name, text))

                # TODO: Use namedtuple
                # Reason why we need getattr here - what's in attr is not
                # bound to the object.
                self._actions_data[name] = (getattr(self, p), text, desc)

    def is_action_allowed(self, name):
        """
            Verify if action with `name` is allowed.

            :param name:
                Action name
        """
        return True

    def get_actions_list(self):
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

    def handle_action(self, return_view=None):
        """
            Handle action request.

            :param return_view:
                Name of the view to return to after the request.
                If not provided, will return user to the return url in the form
                or the list view.
        """
        action = request.form.get('action')
        ids = request.form.getlist('rowid')

        handler = self._actions_data.get(action)

        if handler and self.is_action_allowed(action):
            response = handler[0](ids)

            if response is not None:
                return response

        if return_view:
            url = self.get_url('.' + return_view)
        else:
            url = get_redirect_target() or self.get_url('.index_view')

        return redirect(url)
