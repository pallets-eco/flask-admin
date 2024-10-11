def parse_like_term(term):
    """
        Parse search term into (operation, term) tuple. Recognizes operators
        in the beginning of the search term. Case insensitive is the default.

        * = case sensitive (can precede other operators)
        ^ = starts with
        = = exact

        :param term:
            Search term
    """
    case_sensitive = term.startswith('*')
    if case_sensitive:
        term = term[1:]
    # apply operators
    if term.startswith('^'):
        oper = 'startswith'
        term = term[1:]
    elif term.startswith('='):
        oper = 'exact'
        term = term[1:]
    else:
        oper = 'contains'
    # add case insensitive flag
    if not case_sensitive:
        oper = 'i' + oper
    return oper, term
