def get_primary_key(model):
    return model._meta.primary_key.name


def parse_like_term(term):
    if term.startswith('^'):
        stmt = '%s%%' % term[1:]
    elif term.startswith('='):
        stmt = term[1:]
    else:
        stmt = '%%%s%%' % term

    return stmt


def get_meta_fields(model):
    if hasattr(model._meta, 'sorted_fields'):
        fields = model._meta.sorted_fields
    else:
        fields = model._meta.get_fields()
    return fields
