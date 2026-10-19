import mimetypes
import typing as t

from mongoengine import FileField
from mongoengine import ValidationError
from wtforms.validators import ValidationError as wtfValidationError

from flask_admin._compat import as_unicode
from flask_admin._compat import itervalues


def gridfs_content_type(data: t.Any) -> t.Optional[str]:
    """Return the MIME type for a GridFS ``GridOut``/``GridFSProxy`` without
    triggering PyMongo's ``GridOut.contentType`` deprecation warning (slated
    for removal in PyMongo 5.0).

    Resolution order:

    1. ``data.metadata["content_type"]`` — PyMongo 5.0-compatible location.
    2. Legacy fallback for documents whose content type still lives at the
       deprecated top-level ``contentType`` field (see ``_legacy_content_type``).
    3. ``mimetypes.guess_type(data.filename)`` — best-effort from filename.
    4. ``None`` if no source resolves.
    """
    metadata = getattr(data, "metadata", None) or {}
    if isinstance(metadata, dict):
        ct = metadata.get("content_type")
        if ct:
            return ct

    legacy = _legacy_content_type(data)
    if legacy:
        return legacy

    filename = getattr(data, "filename", None)
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed

    return None


def _legacy_content_type(data: t.Any) -> t.Optional[str]:
    # Reach into the raw BSON doc to avoid PyMongo's GridOut.contentType
    # deprecation warning. Drop this helper when PyMongo 5.0 removes the
    # property (#2920).
    file_doc = getattr(data, "_file", None)
    if isinstance(file_doc, dict):
        return file_doc.get("contentType")
    return None


def make_gridfs_args(value: FileField) -> dict[str, t.Any]:
    args = {"id": value.grid_id, "coll": value.collection_name}

    if value.db_alias != "default":
        args["db"] = value.db_alias

    return args


def make_thumb_args(value: FileField) -> dict[str, t.Any]:
    if getattr(value, "thumbnail", None):
        args = {"id": value.thumbnail._id, "coll": value.collection_name}

        if value.db_alias != "default":
            args["db"] = value.db_alias

        return args
    else:
        return make_gridfs_args(value)


def format_error(error: ValidationError | wtfValidationError | str) -> str:
    if isinstance(error, ValidationError):
        return as_unicode(error)

    if isinstance(error, wtfValidationError):
        return ". ".join(itervalues(error.to_dict()))  # type: ignore[attr-defined]

    return as_unicode(error)
