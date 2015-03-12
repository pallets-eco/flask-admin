from sqlalchemy import tuple_, or_, and_
from sqlalchemy.sql.operators import eq
from sqlalchemy.exc import DBAPIError
from ast import literal_eval

from flask_admin._compat import filter_list
from flask_admin.tools import iterencode, iterdecode, escape


def parse_like_term(term):
    if term.startswith('^'):
        stmt = '%s%%' % term[1:]
    elif term.startswith('='):
        stmt = term[1:]
    else:
        stmt = '%%%s%%' % term

    return stmt


def filter_foreign_columns(base_table, columns):
    """
        Return list of columns that belong to passed table.

        :param base_table: Table to check against
        :param columns: List of columns to filter
    """
    return filter_list(lambda c: c.table == base_table, columns)


def get_primary_key(model):
    """
        Return primary key name from a model. If the primary key consists of multiple columns,
        return the corresponding tuple

        :param model:
            Model class
    """
    mapper = model._sa_class_manager.mapper
    pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]
    if len(pks) == 1:
        return pks[0]
    elif len(pks) > 1:
        return tuple(pks)
    else:
        return None


def has_multiple_pks(model):
    """
        Return True, if the model has more than one primary key
    """
    if not hasattr(model, '_sa_class_manager'):
        raise TypeError('model must be a sqlalchemy mapped model')

    return len(model._sa_class_manager.mapper.primary_key) > 1


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
        Return a query object filtered by primary key values passed in `ids` argument.

        Unfortunately, it is not possible to use `in_` filter if model has more than one
        primary key.
    """
    if has_multiple_pks(model):
        # Decode keys to tuples
        decoded_ids = [iterdecode(v) for v in ids]

        # Get model primary key property references
        model_pk = [getattr(model, name) for name in get_primary_key(model)]

        try:
            query = modelquery.filter(tuple_(*model_pk).in_(decoded_ids))
            # Only the execution of the query will tell us, if the tuple_
            # operator really works
            query.all()
        except DBAPIError:
            query = modelquery.filter(tuple_operator_in(model_pk, decoded_ids))
    else:
        model_pk = getattr(model, get_primary_key(model))
        query = modelquery.filter(model_pk.in_(ids))

    return query
