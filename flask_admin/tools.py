import sys
import traceback
import typing as t
from functools import reduce
from types import ModuleType

# Python 3 compatibility
from ._compat import as_unicode

CHAR_ESCAPE = "."
CHAR_SEPARATOR = ","


def import_module(name: str, required: bool = True) -> ModuleType | None:
    """
    Import module by name

    :param name:
        Module name
    :param required:
        If set to `True` and module was not found - will throw exception.
        If set to `False` and module was not found - will return None.
        Default is `True`.
    """
    try:
        __import__(name, globals(), locals(), [])
    except ImportError:
        if not required and module_not_found():
            return None
        raise
    return sys.modules[name]


def import_attribute(name: str) -> t.Any:
    """
    Import attribute using string reference.

    :param name:
        String reference.

    Raises ImportError or AttributeError if module or attribute do not exist.

    Example::

        import_attribute('a.b.c.foo')

    """
    path, attr = name.rsplit(".", 1)
    module = __import__(path, globals(), locals(), [attr])

    return getattr(module, attr)


def module_not_found(additional_depth: int = 0) -> bool:
    """
    Checks if ImportError was raised because module does not exist or
    something inside it raised ImportError

    :param additional_depth:
        supply int of depth of your call if you're not doing
        import on the same level of code - f.e., if you call function, which is
        doing import, you should pass 1 for single additional level of depth
    """
    tb = sys.exc_info()[2]
    if len(traceback.extract_tb(tb)) > (1 + additional_depth):
        return False
    return True


def rec_getattr(obj: t.Any, attr: str, default: t.Any = None) -> t.Any:
    """
    Recursive getattr.

    :param attr:
        Dot delimited attribute name
    :param default:
        Default value

    Example::

        rec_getattr(obj, 'a.b.c')
    """
    try:
        return reduce(getattr, attr.split("."), obj)
    except AttributeError:
        return default


def get_dict_attr(obj: t.Any, attr: str, default: t.Any = None) -> t.Any | None:
    """
    Get attribute of the object without triggering its __getattr__.

    :param obj:
        Object
    :param attr:
        Attribute name
    :param default:
        Default value if attribute was not found
    """
    for o in [obj] + obj.__class__.mro():
        if attr in o.__dict__:
            return o.__dict__[attr]

    return default


def escape(value: str | bytes) -> str:
    return (
        as_unicode(value)
        .replace(CHAR_ESCAPE, CHAR_ESCAPE + CHAR_ESCAPE)
        .replace(CHAR_SEPARATOR, CHAR_ESCAPE + CHAR_SEPARATOR)
    )


def iterencode(iter: t.Iterable[str | bytes | int]) -> str:
    """
    Encode enumerable as compact string representation.

    :param iter:
        Enumerable
    """
    return ",".join(
        as_unicode(v)
        .replace(CHAR_ESCAPE, CHAR_ESCAPE + CHAR_ESCAPE)
        .replace(CHAR_SEPARATOR, CHAR_ESCAPE + CHAR_SEPARATOR)
        for v in iter
    )


def iterdecode(value: t.Iterable[str]) -> tuple[str, ...]:
    """
    Decode enumerable from string presentation as a tuple
    """

    if not value:
        return tuple()

    result = []
    accumulator = ""

    escaped = False

    for c in value:
        if not escaped:
            if c == CHAR_ESCAPE:
                escaped = True
                continue
            elif c == CHAR_SEPARATOR:
                result.append(accumulator)
                accumulator = ""
                continue
        else:
            escaped = False

        accumulator += c

    result.append(accumulator)

    return tuple(result)
