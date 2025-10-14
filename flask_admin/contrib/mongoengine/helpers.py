import typing as t

from mongoengine import ValidationError
from wtforms.validators import ValidationError as wtfValidationError

from flask_admin._compat import as_unicode
from flask_admin._compat import itervalues


def make_gridfs_args(value):
    args = {"id": value.grid_id, "coll": value.collection_name}

    if value.db_alias != "default":
        args["db"] = value.db_alias

    return args


def make_thumb_args(value):
    if getattr(value, "thumbnail", None):
        args = {"id": value.thumbnail._id, "coll": value.collection_name}

        if value.db_alias != "default":
            args["db"] = value.db_alias

        return args
    else:
        return make_gridfs_args(value)


def format_error(error: t.Union[ValidationError, wtfValidationError, str]):
    if isinstance(error, ValidationError):
        return as_unicode(error)

    if isinstance(error, wtfValidationError):
        return ". ".join(itervalues(error.to_dict()))  # type: ignore[attr-defined]

    return as_unicode(error)
