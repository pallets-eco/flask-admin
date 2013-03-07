def parse_like_term(term):
    """
        Parse search term into (operation, term) tuple. Recognizes operators
        in the begining of the search term.
        
        * = case insensitive (can preceed other operators)
        ^ = starts with
        = = exact

        :param term:
            Search term
    """
    case_insensitive = term.startswith('*')
    if case_insensitive:
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
    if case_insensitive:
        oper = 'i'+oper
    return oper, term
