"""Unit tests for ``flask_admin.contrib.mongoengine.helpers``.

These tests exercise ``gridfs_content_type`` against lightweight fakes so they
run without a live MongoDB instance.
"""

import types

from flask_admin.contrib.mongoengine.helpers import gridfs_content_type


def _fake(**attrs: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**attrs)


def test_prefers_metadata_content_type() -> None:
    data = _fake(
        metadata={"content_type": "image/png"},
        _file={"contentType": "application/legacy"},
        filename="thing.txt",
    )
    assert gridfs_content_type(data) == "image/png"


def test_falls_back_to_legacy_contentType_field() -> None:
    data = _fake(
        metadata={},
        _file={"contentType": "application/pdf"},
        filename="thing.txt",
    )
    assert gridfs_content_type(data) == "application/pdf"


def test_falls_back_to_filename_guess() -> None:
    data = _fake(metadata=None, _file={}, filename="report.txt")
    assert gridfs_content_type(data) == "text/plain"


def test_returns_none_when_nothing_resolves() -> None:
    data = _fake(metadata=None, _file=None, filename=None)
    assert gridfs_content_type(data) is None


def test_returns_none_when_filename_unguessable() -> None:
    data = _fake(metadata={}, _file={}, filename="no-extension")
    assert gridfs_content_type(data) is None


def test_handles_missing_attributes() -> None:
    assert gridfs_content_type(_fake()) is None


def test_non_dict_metadata_is_ignored() -> None:
    data = _fake(
        metadata="not a dict",
        _file={"contentType": "application/pdf"},
        filename=None,
    )
    assert gridfs_content_type(data) == "application/pdf"
