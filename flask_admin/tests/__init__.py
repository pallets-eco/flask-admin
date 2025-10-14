import pytest


def flask_babel_test_decorator(fn):
    """Decorator to annotate any tests that *require* Flask-Babel to be available,
    ie they check translations directly, with the `flask_babel` mark.

    If Flask-Babel is not installed, we add the `xfail` mark to the test so that pytest
    will expect, and therefore ignore, its failure.
    """
    fn = pytest.mark.flask_babel(fn)

    try:
        import flask_babel  # noqa: F401
    except ImportError:
        return pytest.mark.xfail(
            reason="flask-babel is not installed; translations unavailable"
        )(fn)

    return fn
