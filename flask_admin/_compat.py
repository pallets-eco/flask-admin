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

text_type = str
string_types = (str,)

itervalues = lambda d: iter(d.values())
iteritems = lambda d: iter(d.items())
filter_list = lambda f, l: list(filter(f, l))

def as_unicode(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')

    return str(s)

def csv_encode(s):
    ''' Returns unicode string expected by Python 3's csv module '''
    return as_unicode(s)


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})


try:
    # jinja2 3.0.0
    from jinja2 import pass_context
except ImportError:
    from jinja2 import contextfunction as pass_context
