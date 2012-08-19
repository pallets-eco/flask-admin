from flask import request, url_for, redirect


def action(name, text, confirmation=None):
    """
        Use this decorator to expose mass-model actions

        `name`
            Action name
        `text`
            Action text.
            Will be passed through gettext() before rendering.
        `confirmation`
            Confirmation text. If not provided, action will be executed
            unconditionally.
            Will be passed through gettext() before rendering.
    """
    def wrap(f):
        f._action = (name, text, confirmation)
        return f

    return wrap


class ActionsMixin(object):
    def __init__(self):
        self._actions = []
        self._actions_data = {}

    def init_actions(self):
        self._actions = []
        self._actions_data = {}

        for p in dir(self):
            attr = getattr(self, p)

            if hasattr(attr, '_action'):
                name, text, desc = attr._action

                self._actions.append((name, text))

                # TODO: Use namedtuple
                self._actions_data[name] = (attr, text, desc)

    def is_action_allowed(self, name):
        return name not in self.disallowed_actions

    def get_actions_list(self):
        actions = []
        actions_confirmation = {}

        for act in self._actions:
            name, text = act

            if self.is_action_allowed(name):
                text = unicode(text)

                actions.append((name, text))
                actions_confirmation[name] = unicode(self._actions_data[name][2])

        return actions, actions_confirmation

    def handle_action(self, return_view=None):
        action = request.form.get('action')
        ids = request.form.getlist('rowid')

        handler = self._actions_data.get(action)

        if handler and self.is_action_allowed(action):
            response = handler[0](ids)

            if response is not None:
                return response

        if not return_view:
            url = url_for('.' + self._default_view)
        else:
            url = url_for('.' + return_view)

        return redirect(url)
