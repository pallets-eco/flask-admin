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
        Return primary key name from a model. If the primary key consists of multiple columns,
        return the corresponding tuple

        :param model:
            Model class
    """
    props = model._sa_class_manager.mapper.iterate_properties

    pks = []
    for p in props:
        if hasattr(p, 'expression'):    # expression = primary column or expression for this ColumnProperty
            if p.expression.primary_key:
                if is_inherited_primary_key(p):
                    pks.append(get_column_for_current_model(p).key)
                else:
                    pks.append(p.columns[0].key)
    if len(pks) == 1:
        return pks[0]
    elif len(pks) > 1:
        return tuple(pks)
    else:
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
    return (len([column for column in prop.columns if column.primary_key]) == len(prop.columns) and
            len([column for column in prop.columns if column.foreign_keys]) == len(prop.columns) - 1)

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


def has_multiple_pks(model):
    """Return True, if the model has more than one primary key
    """
    if not hasattr(model, '_sa_class_manager'):
        raise TypeError('model must be a sqlalchemy mapped model')
    pks = model._sa_class_manager.mapper.primary_key
    return len(pks) > 1
