from sqlalchemy import tuple_, or_, and_
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.operators import eq
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.selectable import Select, Join

from flask_admin._compat import filter_list, string_types
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


def get_columns_for_field(field):
    if isinstance(field, (ColumnElement, Select, Join)):
        # For hybrid properties
        return [field]

    if hasattr(field, 'property'):
        if hasattr(field.property, 'columns') and field.property.columns:
            return field.property.columns
        # For relationships
        return [field]

    raise Exception('Invalid field %s: does not contains any columns.' % field)


def need_join(model, table):
    """
        Check if join to a table is necessary.
    """
    return table not in model._sa_class_manager.mapper.tables


def get_field_with_path(model, name):
    """
        Resolve property by name and figure out its join path.

        Join path might contain both properties and tables.
    """
    path = []

    # For strings, resolve path
    if isinstance(name, string_types):
        # create a copy to keep original model as `model`
        current_model = model

        for attribute in name.split('.'):
            value = getattr(current_model, attribute)

            if (hasattr(value, 'property') and
                    hasattr(value.property, 'direction')):
                current_model = value.property.mapper.class_

                table = current_model.__table__

                if need_join(model, table):
                    path.append(value)

            attr = value
    else:
        attr = name

        # Determine joins if table.column (relation object) is provided
        if isinstance(attr, InstrumentedAttribute):
            columns = get_columns_for_field(attr)

            if len(columns) > 1:
                raise Exception('Can only handle one column for %s' % name)

            column = columns[0]

            # TODO: Use SQLAlchemy "path-finder" to find exact join path to the target property
            if need_join(model, column.table):
                path.append(column.table)

    return attr, path
