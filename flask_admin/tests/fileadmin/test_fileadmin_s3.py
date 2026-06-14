import typing as t
from io import BytesIO

import boto3
import pytest
from flask import Flask
from moto import mock_aws

from flask_admin import Admin
from flask_admin.contrib.fileadmin.s3 import _strip_leading_slash_from
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

from .test_fileadmin import Base

_bucket_name = "my-bucket"


@pytest.fixture(scope="function", autouse=True)
def mock_s3_client() -> t.Generator[t.Any, None, None]:
    with mock_aws():
        client = boto3.client("s3")
        client.create_bucket(Bucket=_bucket_name)
        client.upload_fileobj(BytesIO(b""), _bucket_name, "dummy.txt")
        yield client


@pytest.mark.parametrize(
    "arg_name, args, kwargs, expected_value",
    (
        ("arg1", ["/some/path", "", ""], {}, "some/path"),
        ("arg2", ["", "/some/path", ""], {}, "some/path"),
        ("arg3", [""], dict(arg2="", arg3="/no/leading"), "no/leading"),
        ("arg1", [], dict(arg1="/", arg2="", arg3=""), ""),
        ("arg1", [], dict(arg1="/something/", arg2="", arg3=""), "something/"),
    ),
)
def test_strip_slashes(
    arg_name: str, args: t.Any, kwargs: t.Any, expected_value: str
) -> None:
    @_strip_leading_slash_from(arg_name)
    def fn(arg1: t.Any, arg2: t.Any, arg3: t.Any) -> dict[str, t.Any]:
        return dict(arg1=arg1, arg2=arg2, arg3=arg3)

    assert fn(*args, **kwargs)[arg_name] == expected_value


class TestS3FileAdmin(Base.FileAdminTests):
    def fileadmin_class(self) -> type[S3FileAdmin]:
        return S3FileAdmin

    def fileadmin_args(self) -> tuple[tuple[t.Any], dict[str, str]]:  # type: ignore[override]
        return (boto3.client("s3"),), {"bucket_name": _bucket_name}

    @pytest.mark.skip
    def test_file_admin_edit(self) -> None:  # type: ignore[override]
        """Override the inherited test as S3FileAdmin has no edit file functionality."""
        pass

    def test_fileadmin_sort_bogus_url_param(self, app: Flask, admin: Admin) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[misc, valid-type]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

    def test_file_upload(self, app: Flask, admin: Admin) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # upload
        rv = client.get("/admin/myfileadmin/upload/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/myfileadmin/upload/",
            data=dict(upload=(BytesIO(b"test content"), "test_upload.txt")),
        )
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "path=test_upload.txt" in rv.text

    def test_file_download(
        self, app: Flask, admin: Admin, mock_s3_client: t.Any
    ) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/myfileadmin/download/dummy.txt")
        assert rv.status_code == 302
        assert rv.headers["Location"].startswith(
            "https://my-bucket.s3.amazonaws.com/dummy.txt?AWSAccessKeyId=FOOBARKEY"
        )

    def test_file_rename(self, app: Flask, admin: Admin, mock_s3_client: t.Any) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # rename
        rv = client.get("/admin/myfileadmin/rename/?path=dummy.txt")
        assert rv.status_code == 200
        assert "dummy.txt" in rv.text

        rv = client.post(
            "/admin/myfileadmin/rename/?path=dummy.txt",
            data=dict(name="dummy_renamed.txt", path="dummy.txt"),
        )
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "path=dummy_renamed.txt" in rv.text
        assert "path=dummy.txt" not in rv.text

    def test_file_delete(self, app: Flask, admin: Admin, mock_s3_client: t.Any) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # delete
        rv = client.post("/admin/myfileadmin/delete/", data=dict(path="dummy.txt"))
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "successfully deleted" in rv.text

    def test_deep_browsing(
        self, app: Flask, admin: Admin, mock_s3_client: t.Any
    ) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            pass

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # create deep path
        rv = client.post("/admin/myfileadmin/mkdir/", data={"name": "xx"})
        rv = client.post("/admin/myfileadmin/mkdir/xx", data={"name": "yy"})
        rv = client.post("/admin/myfileadmin/mkdir/xx/yy", data={"name": "zz"})

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200

        rv = client.get("/admin/myfileadmin/b/xx")
        assert rv.status_code == 200

        rv = client.get("/admin/myfileadmin/b/xx/yy")
        assert rv.status_code == 200

        # Test access to deep path
        rv = client.get("/admin/myfileadmin/b/xx/yy/zz")
        assert rv.status_code == 200
