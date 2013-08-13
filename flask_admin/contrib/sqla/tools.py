def parse_like_term(term):
    if term.startswith('^'):
        stmt = '%s%%' % term[1:]
    elif term.startswith('='):
        stmt = term[1:]
    else:
        stmt = '%%%s%%' % term

    return stmt


def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    props = model._sa_class_manager.mapper.iterate_properties

    for p in props:
        if hasattr(p, 'columns'):
            for c in p.columns:
                if c.primary_key:
                    return p.key

    return None

def is_inherited_primary_key(prop):
    """
        Return True, if the ColumnProperty is an inherited primary key

        Check if all columns are primary keys and _one_ does not have a foreign key -> looks like joined
        table inheritance: http://docs.sqlalchemy.org/en/latest/orm/inheritance.html with "standard
        practice" of same column name.

        :param prop: The ColumnProperty to check
        :return: Boolean
        :raises: Exceptions as they occur - no ExceptionHandling here
    """
    return len([column for column in prop.columns if column.primary_key]) == len(prop.columns) and \
                len([column for column in prop.columns if column.foreign_keys]) == len(prop.columns)-1

def get_column_for_current_model(prop):
    """
        Return the Column() of the ColumnProperty "prop", that refers to the current model

        When using inheritance, a ColumnProperty may contain multiple columns. This function
        returns the Column(), the belongs to the Model of the ColumnProperty - the "current"
        model

        :param prop: The ColumnProperty
        :return: The column for the current model
        :raises: TypeError if not exactely one Column() for the current model could be found.
                    All other Exceptions not handled here but raised
    """
    candidates = [column for column in prop.columns if column.expression == prop.expression]
    if len(candidates) != 1:
        raise TypeError('Not exactly one column for the current model found. ' +
                        'Found %d columns for property %s' % (len(candidates), prop))
    else:
        return candidates[0]

