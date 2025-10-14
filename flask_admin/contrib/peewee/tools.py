from flask_admin._types import T_PEEWEE_FIELD
from flask_admin._types import T_PEEWEE_MODEL


def get_primary_key(model: type[T_PEEWEE_MODEL]) -> str:
    return model._meta.primary_key.name  # type: ignore[attr-defined]


def parse_like_term(term: str) -> str:
    if term.startswith("^"):
        stmt = f"{term[1:]}%"
    elif term.startswith("="):
        stmt = term[1:]
    else:
        stmt = f"%{term}%"

    return stmt


def get_meta_fields(model: type[T_PEEWEE_MODEL]) -> list[T_PEEWEE_FIELD]:
    if hasattr(model._meta, "sorted_fields"):  # type: ignore[attr-defined]
        fields = model._meta.sorted_fields  # type: ignore[attr-defined]
    else:
        fields = model._meta.get_fields()  # type: ignore[attr-defined]
    return fields
