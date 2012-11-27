import sys
import warnings
import traceback


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
        Get attibute of the object without triggering its __getattr__.

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


def get_property(obj, name, old_name, default=None):
    """
        Check if old property name exists and if it is - show warning message
        and return value.

        Otherwise, return new property value

        :param name:
            New property name
        :param old_name:
            Old property name
        :param default:
            Default value
    """
    if hasattr(obj, old_name):
        warnings.warn('Property %s is obsolete, please use %s instead' %
            (old_name, name), stacklevel=2)
        return getattr(obj, old_name)

    return getattr(obj, name, default)


class ObsoleteAttr(object):
    def __init__(self, new_name, old_name, default):
        self.new_name = new_name
        self.old_name = old_name
        self.cache = '_cache_' + new_name
        self.default = default

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Check if we have new cached value
        if hasattr(obj, self.cache):
            return getattr(obj, self.cache)

        # Check if there's old attribute
        if hasattr(obj, self.old_name):
            warnings.warn('Property %s is obsolete, please use %s instead' %
                        (self.old_name, self.new_name), stacklevel=2)
            return getattr(obj, self.old_name)

        # Return default otherwise
        return self.default

    def __set__(self, obj, value):
        setattr(obj, self.cache, value)
