import sys
import traceback


def import_module(name, required=True):
    """
        Import module by name

        `name`
            Module name
        `required`
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

        `name`
            String reference.

        Throws ImportError or AttributeError if module or attribute do not exist.

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

        `additional_depth`
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

        `attr`
            Dot delimited attribute name
        `default`
            Default value

        Example::

            rec_getattr(obj, 'a.b.c')
    """
    try:
        return reduce(getattr, attr.split('.'), obj)
    except AttributeError:
        return default
