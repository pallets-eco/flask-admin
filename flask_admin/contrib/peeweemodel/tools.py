from peewee import PrimaryKeyField


def get_primary_key(model):
    for n, f in model._meta.get_sorted_fields():
        if type(f) == PrimaryKeyField:
            return n


def parse_like_term(term):
    if term.startswith('^'):
        stmt = '%s%%' % term[1:]
    elif term.startswith('='):
        stmt = term[1:]
    else:
        stmt = '%%%s%%' % term

    return stmt
