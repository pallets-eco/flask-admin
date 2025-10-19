import typing as t

from flask_admin._compat import as_unicode
from flask_admin._compat import string_types
from flask_admin.model.ajax import AjaxModelLoader
from flask_admin.model.ajax import DEFAULT_PAGE_SIZE

from ..._types import T_PEEWEE_MODEL
from .tools import get_primary_key


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name: str, model: t.Any, **options: t.Any) -> None:
        """
        Constructor.

        :param fields:
            Fields to run query against
        """
        super().__init__(name, options)

        self.model = model
        self.fields = t.cast(t.Iterable, options.get("fields"))

        if not self.fields:
            raise ValueError(
                f"AJAX loading requires `fields` to be specified for "
                f"{model}.{self.name}"
            )

        self._cached_fields = self._process_fields()

        self.pk = get_primary_key(model)

    def _process_fields(self) -> list[t.Any]:
        remote_fields = []

        for field in self.fields:
            if isinstance(field, string_types):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError(f"{self.model}.{field} does not exist.")

                remote_fields.append(attr)
            else:
                remote_fields.append(field)

        return remote_fields

    def format(self, model: None | str | bytes) -> tuple[t.Any, str] | None:
        if not model:
            return None

        return (getattr(model, self.pk), as_unicode(model))

    def get_one(self, pk: t.Any) -> t.Any:
        return self.model.get(**{self.pk: pk})

    def get_list(
        self, term: str, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE
    ) -> list[t.Any]:
        query = self.model.select()

        if len(term) > 0:
            stmt = None
            for field in self._cached_fields:
                q = field ** (f"%{term}%")

                if stmt is None:
                    stmt = q
                else:
                    stmt |= q

            query = query.where(stmt)

        if offset:
            query = query.offset(offset)

        return list(query.limit(limit).execute())


def create_ajax_loader(
    model: type[T_PEEWEE_MODEL],
    name: str,
    field_name: str,
    options: dict[str, t.Any] | list | tuple,
) -> QueryAjaxModelLoader:
    prop = getattr(model, field_name, None)

    if prop is None:
        raise ValueError(f"Model {model} does not have field {field_name}.")

    # TODO: Check for field
    remote_model = prop.rel_model
    return QueryAjaxModelLoader(name, remote_model, **options)  # type: ignore[arg-type]
