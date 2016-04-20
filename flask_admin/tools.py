import sys
import traceback

# Python 3 compatibility
from ._compat import reduce, as_unicode

CHAR_ESCAPE = u'.'
CHAR_SEPARATOR = u','


def import_module(name, required=True):
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


def import_attribute(name):
    """
        Import attribute using string reference.

        :param name:
            String reference.

        Raises ImportError or AttributeError if module or attribute do not exist.

        Example::

            import_attribute('a.b.c.foo')

    """
    path, attr = name.rsplit('.', 1)
    module = __import__(path, globals(), locals(), [attr])

    return getattr(module, attr)


def module_not_found(additional_depth=0):
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


def rec_getattr(obj, attr, default=None):
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
        return reduce(getattr, attr.split('.'), obj)
    except AttributeError:
        return default


def get_dict_attr(obj, attr, default=None):
    """
        Get attribute of the object without triggering its __getattr__.

        :param obj:
            Object
        :param attr:
            Attribute name
        :param default:
            Default value if attribute was not found
    """
    for obj in [obj] + obj.__class__.mro():
        if attr in obj.__dict__:
            return obj.__dict__[attr]

    return default


def escape(value):
    return (as_unicode(value)
            .replace(CHAR_ESCAPE, CHAR_ESCAPE + CHAR_ESCAPE)
            .replace(CHAR_SEPARATOR, CHAR_ESCAPE + CHAR_SEPARATOR))


def iterencode(iter):
    """
        Encode enumerable as compact string representation.

        :param iter:
            Enumerable
    """
    return ','.join(as_unicode(v)
                    .replace(CHAR_ESCAPE, CHAR_ESCAPE + CHAR_ESCAPE)
                    .replace(CHAR_SEPARATOR, CHAR_ESCAPE + CHAR_SEPARATOR)
                    for v in iter)

def iterdecode(value):
    """
        Decode enumerable from string presentation as a tuple
    """

    if not value:
        return tuple()

    result = []
    accumulator = u''

    escaped = False

    for c in value:
        if not escaped:
            if c == CHAR_ESCAPE:
                escaped = True
                continue
            elif c == CHAR_SEPARATOR:
                result.append(accumulator)
                accumulator = u''
                continue
        else:
            escaped = False

        accumulator += c

    result.append(accumulator)

    return tuple(result)
