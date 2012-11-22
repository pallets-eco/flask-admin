def parse_like_term(term):
    if term.startswith('^'):
        return 'startswith', term[1:]
    elif term.startswith('='):
        return 'exact', term[1:]

    return 'contains', term
