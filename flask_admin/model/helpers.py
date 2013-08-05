def prettify_name(name):
    """
        Prettify pythonic variable name.

        For example, 'hello_world' will be converted to 'Hello World'

        :param name:
            Name to prettify
    """
    return name.replace('_', ' ').title()
