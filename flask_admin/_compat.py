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

import typing as t
from types import MappingProxyType
from flask_admin._types import T_TRANSLATABLE, T_ITER_CHOICES

text_type = str
string_types = (str,)

K = t.TypeVar("K")
V = t.TypeVar("V")


def itervalues(d: dict[t.Any, V]) -> t.Iterator[V]:
    return iter(d.values())


def iteritems(
    d: dict[K, V] | MappingProxyType[K, V] | t.Mapping[K, V],
) -> t.ItemsView[K, V]:
    return d.items()


T = t.TypeVar("T")


def filter_list(f: t.Callable[[t.Any], bool], l: t.Sequence[T]) -> list[T]:
    return list(filter(f, l))


def as_unicode(s: t.Any) -> str:
    if isinstance(s, bytes):
        return s.decode("utf-8")

    return str(s)


def csv_encode(s: str | bytes) -> str:
    """Returns unicode string expected by Python 3's csv module"""
    return as_unicode(s)


def _iter_choices_wtforms_compat(
    val: str, label: T_TRANSLATABLE, selected: bool
) -> T_ITER_CHOICES:
    """Compatibility for 3-tuples and 4-tuples in iter_choices

    https://wtforms.readthedocs.io/en/3.2.x/changes/#version-3-2-0
    """
    import wtforms

    wtforms_version = tuple(int(part) for part in wtforms.__version__.split(".")[:2])

    if wtforms_version >= (3, 2):
        return val, label, selected, {}

    return val, label, selected
