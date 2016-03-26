def macro(name):
    """
        Resolve macro in a Jinja2 context

        :param context:
            Jinja2 context
        :param name:
            Macro name. May be full path (with dots)
    """
    def inner(view, context, model, column):
        parts = name.split('.')
        field = context.resolve(parts[0])

        if not field:
            return None

        for p in parts[1:]:
            field = getattr(field, p, None)

            if not field:
                return field

        return field(model=model, column=column)

    return inner


