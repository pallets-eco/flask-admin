from sqlalchemy import tuple_, or_, and_
from sqlalchemy.sql.operators import eq
from sqlalchemy.exc import DBAPIError
from ast import literal_eval

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
                    pks.append(p.key)
        else:
            if hasattr(p, 'columns'):
                for c in p.columns:
                    if c.primary_key:
                        pks.append(p.key)
                        break

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
    if not hasattr(prop, 'expression'):
        return False

    if prop.expression.primary_key:
        return len(prop._orig_columns) == len(prop.columns)-1

    return False

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

def tuple_operator_in(model_pk, ids):
    """The tuple_ Operator only works on certain engines like MySQL or Postgresql. It does not work with sqlite.

    The function returns an or_ - operator, that containes and_ - operators for every single tuple in ids.

    Example::

      model_pk =  [ColumnA, ColumnB]
      ids = ((1,2), (1,3))

      tuple_operator(model_pk, ids) -> or_( and_( ColumnA == 1, ColumnB == 2), and_( ColumnA == 1, ColumnB == 3) )

    The returning operator can be used within a filter(), as it is just an or_ operator
    """
    l = []
    for id in ids:
        k = []
        for i in range(len(model_pk)):
            k.append(eq(model_pk[i],id[i]))
        l.append(and_(*k))
    if len(l)>=1:
        return or_(*l)
    else:
        return None


def get_query_for_ids(modelquery, model, ids):
    """
        Return a query object, that contains all entities of the given model for
        the primary keys provided in the ids-parameter.

        The ``pks`` parameter is a tuple, that contains the different primary key values,
        that should be returned. If the primary key of the model consists of multiple columns
        every entry of the ``pks`` parameter must be a tuple containing the columns-values in the
        correct order, that make up the primary key of the model

        If the model has multiple primary keys, the
        `tuple_ <http://docs.sqlalchemy.org/en/latest/core/expression_api.html#sqlalchemy.sql.expression.tuple_>`_
        operator will be used. As this operator does not work on certain databases,
        notably on sqlite, a workaround function :func:`tuple_operator_in` is provided
        that implements the same logic using OR and AND operations.

        When having multiple primary keys, the pks are provided as a list of tuple-look-alike-strings,
        ``[u'(1, 2)', u'(1, 1)']``. These needs to be evaluated into real tuples, where
        `Stackoverflow Question 3945856 <http://stackoverflow.com/questions/3945856/converting-string-to-tuple-and-adding-to-tuple>`_
        pointed to `Literal Eval <http://docs.python.org/2/library/ast.html#ast.literal_eval>`_, which is now used.
    """
    if has_multiple_pks(model):
        model_pk = [getattr(model, pk_name).expression for pk_name in get_primary_key(model)]
        ids = [literal_eval(id) for id in ids]
        try:
            query = modelquery.filter(tuple_(*model_pk).in_(ids))
            # Only the execution of the query will tell us, if the tuple_
            # operator really works
            query.all()
        except DBAPIError:
            query = modelquery.filter(tuple_operator_in(model_pk, ids))
    else:
        model_pk = getattr(model, get_primary_key(model))
        query = modelquery.filter(model_pk.in_(ids))
    return query
