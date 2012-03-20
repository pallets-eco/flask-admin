import sys, traceback


def import_module(name, required=True):
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
    Example:
    import_attribute('a.b.c.foo')
    Throws ImportError or AttributeError if module or attribute do not exist.
    """
    path, attr = name.rsplit('.', 1)
    module = __import__(path, globals(), locals(), [attr])

    return getattr(module, attr)


def module_not_found(additional_depth=0):
    '''Checks if ImportError was raised because module does not exist or
    something inside it raised ImportError

     - additional_depth - supply int of depth of your call if you're not doing
       import on the same level of code - f.e., if you call function, which is
       doing import, you should pass 1 for single additional level of depth
    '''
    tb = sys.exc_info()[2]
    if len(traceback.extract_tb(tb)) > (1 + additional_depth):
        return False
    return True


def rec_getattr(obj, attr, default=None):
    try:
        return reduce(getattr, attr.split('.'), obj)
    except AttributeError:
        return None

