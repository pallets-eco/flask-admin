import re


def parse_like_term(term):
    """
    Parse search term into (operation, term) tuple

    :param term:
        Search term
    """
    if term.startswith("^"):
        return f"^{re.escape(term[1:])}"
    elif term.startswith("="):
        return f"^{re.escape(term[1:])}$"

    return re.escape(term)
