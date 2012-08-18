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
