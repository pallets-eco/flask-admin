"""
flask_admin._backwards
~~~~~~~~~~~~~~~~~~~~~~~~~~

Backward compatibility helpers.
"""

import sys
import warnings


def get_property(obj, name, old_name, default=None):
    """
    Check if old property name exists and if it does - show warning message
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
        warnings.warn(
            f"Property {old_name} is obsolete, please use {name} instead",
            stacklevel=2,
        )
        return getattr(obj, old_name)

    return getattr(obj, name, default)


class ObsoleteAttr:
    def __init__(self, new_name, old_name, default):
        self.new_name = new_name
        self.old_name = old_name
        self.cache = "_cache_" + new_name
        self.default = default

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Check if we have new cached value
        if hasattr(obj, self.cache):
            return getattr(obj, self.cache)

        # Check if there's old attribute
        if hasattr(obj, self.old_name):
            warnings.warn(
                (
                    f"Property {self.old_name} is obsolete, please use {self.new_name} "
                    f"instead"
                ),
                stacklevel=2,
            )
            return getattr(obj, self.old_name)

        # Return default otherwise
        return self.default

    def __set__(self, obj, value):
        setattr(obj, self.cache, value)


class ImportRedirect:
    def __init__(self, prefix, target):
        self.prefix = prefix
        self.target = target

    def find_module(self, fullname, path=None):
        if fullname.startswith(self.prefix):
            return self

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        path = self.target + fullname[len(self.prefix) :]
        __import__(path)

        module = sys.modules[fullname] = sys.modules[path]
        return module


def import_redirect(old, new):
    sys.meta_path.append(ImportRedirect(old, new))
