def macro(name):
    '''
        Jinja2 macro list column formatter.

        :param name:
            Macro name in the current template
    '''
    def inner(view, context, model, column):
        m = context.resolve(name)

        if not m:
            return m

        return m(model=model, column=column)

    return inner
