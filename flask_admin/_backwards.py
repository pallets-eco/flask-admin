"""
flask_admin._backwards
~~~~~~~~~~~~~~~~~~~~~~~~~~

Backward compatibility helpers.
"""

import sys
import typing as t
import warnings
from types import ModuleType


def get_property(obj: t.Any, name: str, old_name: str, default: t.Any = None) -> t.Any:
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
    def __init__(self, new_name: str, old_name: str, default: t.Any):
        self.new_name = new_name
        self.old_name = old_name
        self.cache = "_cache_" + new_name
        self.default = default

    def __get__(self, obj: t.Any, objtype: t.Optional[type] = None) -> "ObsoleteAttr":
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

    def __set__(self, obj: t.Any, value: t.Any) -> None:
        setattr(obj, self.cache, value)


class ImportRedirect:
    def __init__(self, prefix: str, target: str):
        self.prefix = prefix
        self.target = target

    def find_module(
        self, fullname: str, path: t.Optional[str] = None
    ) -> t.Optional["ImportRedirect"]:
        if fullname.startswith(self.prefix):
            return self
        return None

    def load_module(self, fullname: str) -> ModuleType:
        if fullname in sys.modules:
            return sys.modules[fullname]

        path = self.target + fullname[len(self.prefix) :]
        __import__(path)

        module = sys.modules[fullname] = sys.modules[path]
        return module


def import_redirect(old: str, new: str) -> None:
    sys.meta_path.append(ImportRedirect(old, new))  # type: ignore[arg-type]
