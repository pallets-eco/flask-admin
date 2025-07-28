"""
SQLModel AJAX support for Flask-Admin.

This module provides AJAX-based model loading functionality for SQLModel models,
enabling dynamic population of form fields with related model data.
"""

import typing as t
from typing import Any
from typing import Optional

from sqlmodel import cast
from sqlmodel import or_
from sqlmodel import select
from sqlmodel import String

# Import from sqlalchemy for functions not in sqlmodel
try:
    from sqlmodel import and_
    from sqlmodel import text
except ImportError:
    from sqlalchemy import and_
    from sqlalchemy import text

from flask_admin._compat import as_unicode
from flask_admin._compat import string_types

# Import centralized types
from flask_admin.contrib.sqlmodel._types import T_SQLMODEL
from flask_admin.contrib.sqlmodel._types import T_SQLMODEL_PK_VALUE
from flask_admin.contrib.sqlmodel._types import T_SQLMODEL_SESSION_TYPE
from flask_admin.model.ajax import AjaxModelLoader
from flask_admin.model.ajax import DEFAULT_PAGE_SIZE

from .tools import get_primary_key
from .tools import has_multiple_pks
from .tools import is_relationship


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(
        self,
        name: str,
        session: T_SQLMODEL_SESSION_TYPE,
        model: type[T_SQLMODEL],
        **options: t.Any,
    ) -> None:
        """
        Constructor.

        :param fields:
            Fields to run query against
        :param filters:
            Additional filters to apply to the loader
        """
        super().__init__(name, options)

        self.session = session
        self.model = model
        self.fields: Optional[list[t.Any]] = options.get("fields")
        self.order_by = options.get("order_by")
        self.filters = options.get("filters")

        if not self.fields:
            raise ValueError(
                f"AJAX loading requires `fields` to be specified for"
                f" {model}.{self.name}"
            )

        self._cached_fields = self._process_fields()

        if has_multiple_pks(model):
            raise NotImplementedError(
                "Flask-Admin does not support multi-pk AJAX model loading."
            )

        pk_result = get_primary_key(model)  # Single PK only, checked above
        self.pk = str(pk_result) if pk_result is not None else "id"

    def _process_fields(self) -> list[Any]:
        remote_fields = []

        for field in self.fields or []:
            if isinstance(field, string_types):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError(f"{self.model}.{field} does not exist.")

                remote_fields.append(attr)
            else:
                # Direct SQLModel field or computed property
                remote_fields.append(field)

        return remote_fields

    def format(self, model: t.Any) -> t.Optional[tuple[t.Any, str]]:
        if not model:
            return None

        pk_value: T_SQLMODEL_PK_VALUE = getattr(model, str(self.pk))
        return pk_value, as_unicode(model)

    def get_query(self) -> t.Any:
        # For compatibility, return session.query if available, otherwise select
        if hasattr(self.session, "query"):
            return self.session.query(self.model)
        else:
            return select(self.model)

    def get_one(self, pk: t.Any) -> Optional[T_SQLMODEL]:
        # prevent autoflush from occurring during populate_obj
        with self.session.no_autoflush:  # type: ignore[attr-defined]
            # Import tools here to avoid circular import
            from . import tools

            # Convert string primary key to proper type if needed
            converted_pk = tools.convert_pk_value(
                pk, tools.get_primary_key_types(self.model).get(str(self.pk), str)
            )
            stmt: t.Any = select(self.model).where(
                getattr(self.model, str(self.pk)) == converted_pk
            )
            return self.session.scalar(stmt)

    def get_list(
        self, term: str, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE
    ) -> list[T_SQLMODEL]:
        # Start with a select statement that returns ORM objects
        stmt: t.Any = select(self.model)

        # Apply filters
        filters = (
            cast(field, String).ilike(f"%{term}%") for field in self._cached_fields
        )
        stmt = stmt.filter(or_(*filters))

        if self.filters:
            # Get tablename safely
            tablename = getattr(self.model, "__tablename__", None)
            if tablename and hasattr(tablename, "lower"):
                tablename_str = tablename.lower()
            elif isinstance(tablename, str):
                tablename_str = tablename.lower()
            else:
                tablename_str = str(self.model.__name__).lower()

            filter_expressions = [
                text(f"{tablename_str}.{value}") for value in self.filters
            ]
            stmt = stmt.filter(and_(*filter_expressions))

        if self.order_by:
            stmt = stmt.order_by(self.order_by)

        # Use scalars() to get ORM objects instead of Row objects
        return self.session.scalars(stmt.offset(offset).limit(limit)).all()


def create_ajax_loader(
    model: type[T_SQLMODEL],
    session: T_SQLMODEL_SESSION_TYPE,
    name: str,
    field_name: str,
    options: dict[str, t.Any],
) -> QueryAjaxModelLoader:
    attr = getattr(model, field_name, None)

    if attr is None:
        raise ValueError(f"Model {model} does not have field {field_name}.")

    if not is_relationship(attr):
        raise ValueError(f"{model}.{field_name} is not a relation.")

    # For SQLModel, get the relationship target model
    remote_model = attr.property.mapper.class_
    return QueryAjaxModelLoader(name, session, remote_model, **options)
