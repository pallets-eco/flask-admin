import types
import typing as t

from sqlalchemy import and_
from sqlalchemy import inspect
from sqlalchemy import or_
from sqlalchemy import tuple_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.clsregistry import _class_resolver
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Table

from flask_admin._types import T_ORM_MODEL
from flask_admin._types import T_SQLALCHEMY_MODEL

try:
    # SQLAlchemy 2.0
    from sqlalchemy.ext.associationproxy import (  # type: ignore[attr-defined]
        AssociationProxyExtensionType,
    )

    ASSOCIATION_PROXY = AssociationProxyExtensionType.ASSOCIATION_PROXY
except ImportError:
    from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY

from sqlalchemy.exc import DBAPIError
from sqlalchemy.sql.operators import eq  # type: ignore[attr-defined]

from flask_admin._compat import filter_list
from flask_admin._compat import string_types
from flask_admin.tools import escape  # noqa: F401
from flask_admin.tools import iterdecode  # noqa: F401
from flask_admin.tools import iterencode  # noqa: F401


def parse_like_term(term: str) -> str:
    if term.startswith("^"):
        stmt = f"{term[1:]}%"
    elif term.startswith("="):
        stmt = term[1:]
    else:
        stmt = f"%{term}%"

    return stmt


def filter_foreign_columns(base_table: Table, columns: list) -> list:
    """
    Return list of columns that belong to passed table.

    :param base_table: Table to check against
    :param columns: List of columns to filter
    """
    return filter_list(lambda c: c.table == base_table, columns)


def get_primary_key(
    model: type[T_ORM_MODEL],
) -> t.Union[tuple[t.Any, ...], t.Any]:
    """
    Return primary key name from a model. If the primary key consists of multiple
    columns, return the corresponding tuple

    :param model:
        Model class
    """
    mapper = model._sa_class_manager.mapper  # type: ignore[union-attr]
    pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]
    if len(pks) == 1:
        return pks[0]
    elif len(pks) > 1:
        return tuple(pks)
    else:
        return None


def has_multiple_pks(model: type[T_SQLALCHEMY_MODEL]) -> bool:
    """
    Return True, if the model has more than one primary key
    """
    if not hasattr(model, "_sa_class_manager"):
        raise TypeError("model must be a sqlalchemy mapped model")

    return len(model._sa_class_manager.mapper.primary_key) > 1


def tuple_operator_in(
    model_pk: t.Sequence[t.Any], ids: tuple[tuple[t.Any, ...], ...]
) -> t.Any:
    """The tuple_ Operator only works on certain engines like MySQL or Postgresql. It
    does not work with sqlite.

    The function returns an or_ - operator, that containes and_ - operators for every
    single tuple in ids.

    Example::

      model_pk =  [ColumnA, ColumnB]
      ids = ((1,2), (1,3))

      tuple_operator(model_pk, ids)
      ->
      or_( and_( ColumnA == 1, ColumnB == 2), and_( ColumnA == 1, ColumnB == 3) )

    The returning operator can be used within a filter(), as it is just an or_ operator
    """
    ands = []
    for id in ids:
        k = []
        for i in range(len(model_pk)):
            k.append(eq(model_pk[i], id[i]))
        ands.append(and_(*k))
    if len(ands) >= 1:
        return or_(*ands)
    else:
        return None


def get_query_for_ids(
    modelquery: t.Any, model: type[T_SQLALCHEMY_MODEL], ids: tuple
) -> t.Any:
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
            query = modelquery.filter(
                tuple_operator_in(
                    model_pk,
                    decoded_ids,  # type: ignore[arg-type]
                )
            )
    else:
        model_pk = getattr(
            model,
            get_primary_key(model),  # type: ignore[arg-type]
        )
        query = modelquery.filter(model_pk.in_(ids))

    return query


def get_columns_for_field(
    field: t.Union[InstrumentedAttribute, ColumnProperty],
) -> list[Column]:
    if (
        not field
        or not hasattr(field, "property")
        or not hasattr(field.property, "columns")
        or not field.property.columns
    ):
        raise Exception(f"Invalid field {field}: does not contains any columns.")

    return field.property.columns


def need_join(model: type[T_SQLALCHEMY_MODEL], table: Table) -> bool:
    """
    Check if join to a table is necessary.
    """
    return table not in model._sa_class_manager.mapper.tables  # type: ignore[attr-defined]


def get_field_with_path(
    model: type[T_SQLALCHEMY_MODEL],
    name: t.Union[str, InstrumentedAttribute, ColumnProperty],
    return_remote_proxy_attr: bool = True,
) -> tuple[t.Optional[t.Any], list]:
    """
    Resolve property by name and figure out its join path.

    Join path might contain both properties and tables.
    """
    path = []

    # For strings, resolve path
    if isinstance(name, string_types):
        # create a copy to keep original model as `model`
        current_model = model

        value = None
        for attribute in name.split("."):
            value = getattr(current_model, attribute)

            if is_association_proxy(value):
                relation_values = value.attr
                if return_remote_proxy_attr:
                    value = value.remote_attr
            else:
                relation_values = [value]

            for relation_value in relation_values:
                if is_relationship(relation_value):
                    current_model = relation_value.property.mapper.class_
                    table = current_model.__table__
                    if need_join(model, table):
                        path.append(relation_value)

        attr = value
    else:
        attr = name

        # Determine joins if table.column (relation object) is provided
        if isinstance(attr, InstrumentedAttribute) or is_association_proxy(attr):
            columns = get_columns_for_field(attr)

            if len(columns) > 1:
                raise Exception(f"Can only handle one column for {name}")

            column = columns[0]

            # TODO: Use SQLAlchemy "path-finder" to find exact join path to the
            #  target property
            if need_join(model, column.table):
                path.append(column.table)

    return attr, path


# copied from sqlalchemy-utils
def get_hybrid_properties(
    model: type[T_SQLALCHEMY_MODEL],
) -> dict[str, hybrid_property]:
    return dict(
        (key, prop)
        for key, prop in inspect(model).all_orm_descriptors.items()
        if isinstance(prop, hybrid_property)
    )


def is_hybrid_property(model: type[T_SQLALCHEMY_MODEL], attr_name: str) -> bool:
    if isinstance(attr_name, string_types):
        names = attr_name.split(".")
        last_model = model
        for i in range(len(names) - 1):
            attr = getattr(last_model, names[i])
            if is_association_proxy(attr):
                attr = attr.remote_attr
            last_model = attr.property.argument
            if isinstance(last_model, string_types):
                last_model = attr.property._clsregistry_resolve_name(last_model)()
            elif isinstance(last_model, _class_resolver):
                last_model = model._decl_class_registry[last_model.arg]  # type: ignore[attr-defined]
            elif isinstance(last_model, (types.FunctionType, types.MethodType)):
                last_model = last_model()
        last_name = names[-1]
        return last_name in get_hybrid_properties(last_model)
    else:
        return attr_name.name in get_hybrid_properties(model)


def is_relationship(attr: InstrumentedAttribute) -> bool:
    return hasattr(attr, "property") and hasattr(attr.property, "direction")


def is_association_proxy(attr: t.Union[ColumnProperty, InstrumentedAttribute]) -> bool:
    if hasattr(attr, "parent"):
        attr = attr.parent
    return hasattr(attr, "extension_type") and attr.extension_type == ASSOCIATION_PROXY
