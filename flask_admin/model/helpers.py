def prettify_name(name):
    """
        Prettify pythonic variable name.

        For example, 'hello_world' will be converted to 'Hello World'

        :param name:
            Name to prettify
    """
    return name.replace('_', ' ').title()

def get_mdict_item_or_list(mdict, key):
    """
        Return the value for the given key of the multidict.

        A werkzeug.datastructures.multidict can have a single
        value or a list of items. If there is only one item,
        return only this item, else the whole list as a tuple

        :param mdict: Multidict to search for the key
        :type mdict: werkzeug.datastructures.multidict
        :param key: key to look for
        :return: the value for the key or None if the Key has not be found
    """
    if hasattr(mdict, 'getlist'):
        v = mdict.getlist(key)
        if len(v) == 1:
            value = v[0]

            # Special case for empty strings, treat them as "no-value"
            if value == '':
                value = None

            return value
        elif len(v) == 0:
            return None
        else:
            return tuple(v)
    return None
