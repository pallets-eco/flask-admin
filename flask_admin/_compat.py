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
from enum import Enum
from enum import EnumMeta
from types import MappingProxyType

import wtforms
import wtforms.fields

from flask_admin._types import T_CHOICE_ITEM
from flask_admin._types import T_CHOICES
from flask_admin._types import T_CHOICES_ITERABLE
from flask_admin._types import T_ITER_CHOICES
from flask_admin._types import T_TRANSLATABLE

text_type = str
string_types = (str,)

_WTFORMS_VERSION = tuple(int(part) for part in wtforms.__version__.split(".")[:2])
_WTFORMS_CHOICE: type[t.Any] | None = getattr(wtforms.fields, "Choice", None)
_WTFORMS_SELECT_CHOICE: type[t.Any] | None = getattr(
    wtforms.fields, "SelectChoice", None
)

K = t.TypeVar("K")
V = t.TypeVar("V")


def itervalues(d: dict[t.Any, V]) -> t.Iterator[V]:
    return iter(d.values())


def iteritems(
    d: dict[K, V] | MappingProxyType[K, V] | t.Mapping[K, V],
) -> t.Iterator[tuple[K, V]]:
    return iter(d.items())


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
    val: t.Any,
    label: T_TRANSLATABLE,
    selected: bool,
    render_kw: dict[str, t.Any] | None = None,
) -> T_ITER_CHOICES:
    """Compatibility for Choice, 4-tuples, and 3-tuples in ``iter_choices``.

    - WTForms >= 3.3 expects ``wtforms.fields.Choice`` instances.
    - WTForms 3.2 expects 4-tuples ``(value, label, selected, render_kw)``.
    - WTForms < 3.2 expects 3-tuples ``(value, label, selected)``.

    https://wtforms.readthedocs.io/en/3.2.x/changes/#version-3-2-0
    """
    if _WTFORMS_CHOICE is not None:
        return _WTFORMS_CHOICE(
            value=val,
            label=label,
            selected=selected,
            render_kw=render_kw or {},
        )

    if _WTFORMS_VERSION >= (3, 2):
        return val, label, selected, render_kw or {}

    return val, label, selected


def _to_select_choice(
    item: T_CHOICE_ITEM, optgroup: str | None = None
) -> T_CHOICE_ITEM:
    if _WTFORMS_SELECT_CHOICE is None:
        return item

    if isinstance(item, _WTFORMS_SELECT_CHOICE):
        if optgroup and not item.optgroup:
            return _WTFORMS_SELECT_CHOICE(
                value=item.value,
                label=item.label,
                render_kw=item.render_kw,
                optgroup=optgroup,
            )
        return item

    if isinstance(item, tuple) and len(item) in (2, 3):
        return _WTFORMS_SELECT_CHOICE(*item, optgroup=optgroup)

    if isinstance(item, Enum):
        return _WTFORMS_SELECT_CHOICE(
            value=item.value, label=item.name, optgroup=optgroup
        )

    if isinstance(item, str) and optgroup is not None:
        return _WTFORMS_SELECT_CHOICE(value=item, optgroup=optgroup)

    return item


def _choices_wtforms_compat(choices: T_CHOICES) -> T_CHOICES:
    """Convert legacy tuple/dict/Enum choices to ``SelectChoice`` on WTForms >= 3.3.

    On WTForms < 3.3, returns ``choices`` unchanged.
    """
    if _WTFORMS_SELECT_CHOICE is None or choices is None:
        return choices

    if isinstance(choices, EnumMeta):
        members: t.Iterable[Enum] = choices
        return [
            _WTFORMS_SELECT_CHOICE(value=member.value, label=member.name)
            for member in members
        ]

    if callable(choices):
        return choices

    if isinstance(choices, t.Mapping):
        result: list[T_CHOICE_ITEM] = []
        for key, value in choices.items():
            if isinstance(value, t.Mapping):
                for inner_val, inner_label in value.items():
                    result.append(
                        _WTFORMS_SELECT_CHOICE(
                            value=inner_val, label=inner_label, optgroup=key
                        )
                    )
            elif isinstance(value, list | tuple | set):
                for item in value:
                    result.append(_to_select_choice(item, optgroup=key))
            else:
                result.append(_WTFORMS_SELECT_CHOICE(value=key, label=value))
        return result

    return [_to_select_choice(item) for item in choices]


def _unpack_choice(
    choice: T_CHOICE_ITEM,
) -> tuple[t.Any, T_TRANSLATABLE, dict[str, t.Any]]:
    """Extract ``(value, label, render_kw)`` from a ``SelectChoice``, ``Choice``,
    tuple, ``Enum`` member, or ``str``.
    """
    if _WTFORMS_SELECT_CHOICE is not None and isinstance(
        choice, _WTFORMS_SELECT_CHOICE
    ):
        return choice.value, choice.label, choice.render_kw or {}

    if _WTFORMS_CHOICE is not None and isinstance(choice, _WTFORMS_CHOICE):
        return choice.value, choice.label, choice.render_kw or {}

    if isinstance(choice, tuple):
        render_kw = choice[2] if len(choice) > 2 and choice[2] else {}
        return choice[0], choice[1], render_kw

    if isinstance(choice, Enum):
        return choice.value, choice.name, {}

    if isinstance(choice, str):
        return choice, choice, {}

    return choice.value, choice.label, choice.render_kw or {}


def _iter_raw_choices(
    choices: T_CHOICES_ITERABLE | None,
) -> t.Iterator[tuple[t.Any, T_TRANSLATABLE, dict[str, t.Any]]]:
    """Yield ``(value, label, render_kw)`` tuples from any supported ``choices``."""
    if choices is None:
        return

    if isinstance(choices, EnumMeta):
        members: t.Iterable[Enum] = choices
        for member in members:
            yield member.value, member.name, {}
        return

    if isinstance(choices, t.Mapping):
        for key, value in choices.items():
            if isinstance(value, t.Mapping):
                for inner_val, inner_label in value.items():
                    yield inner_val, inner_label, {}
            elif isinstance(value, list | tuple | set):
                for item in value:
                    yield _unpack_choice(item)
            else:
                yield key, value, {}
        return

    for choice in choices:
        yield _unpack_choice(choice)
