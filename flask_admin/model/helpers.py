def get_default_order(view):
    """
        Get default sort order from model view.

        Returns (field, desc) tuple.

        :param view:
            View instance
    """
    if view.column_default_sort:
        if isinstance(view.column_default_sort, tuple):
            return view.column_default_sort
        else:
            return (view.column_default_sort, False)

    return None
