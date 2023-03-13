def setup():
    import warnings
    warnings.warn('Flask-Admin peewee integration module was renamed as '
                  'flask_admin.contrib.peewee, please use it instead.')

    from flask_admin._backwards import import_redirect
    import_redirect(__name__, 'flask_admin.contrib.peewee')


setup()
del setup

from ..peewee.view import ModelView  # noqa: F401
