from flask import g


def set_current_view(view):
    g._admin_view = view


def get_current_view():
    return getattr(g, '_admin_view', None)
