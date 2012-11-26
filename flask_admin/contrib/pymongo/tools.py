def parse_like_term(term):
    """
        Parse search term into (operation, term) tuple

        :param term:
            Search term
    """
    if term.startswith('^'):
        return '^%s' % term[1]
    elif term.startswith('='):
        return '^%s$' % term[1:]

    return '%s' % term
