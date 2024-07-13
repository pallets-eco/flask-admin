# flake8: noqa
"""
    flask_admin._compat
    ~~~~~~~~~~~~~~~~~~~~~~~

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: (c) 2013 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from typing import Callable

text_type = str
string_types = (str,)


def itervalues(d: dict):
    return iter(d.values())


def iteritems(d: dict):
    return iter(d.items())


def filter_list(f: Callable, l: list):
    return list(filter(f, l))


def as_unicode(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')

    return str(s)

def csv_encode(s):
    ''' Returns unicode string expected by Python 3's csv module '''
    return as_unicode(s)


try:
    # jinja2 3.0.0
    from jinja2 import pass_context  # type: ignore[attr-defined]
except ImportError:
    from jinja2 import contextfunction as pass_context
