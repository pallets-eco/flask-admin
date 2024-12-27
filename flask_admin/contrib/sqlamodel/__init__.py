def setup():
    import warnings

    warnings.warn(
        "Flask-Admin sqlalchemy integration module was renamed as "
        "flask_admin.contrib.sqla, please use it instead.",
        stacklevel=1,
    )

    from flask_admin._backwards import import_redirect

    import_redirect(__name__, "flask_admin.contrib.sqla")


setup()
del setup

from ..sqla.view import ModelView  # noqa: F401, E402
