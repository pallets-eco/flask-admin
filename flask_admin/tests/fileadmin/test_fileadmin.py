import os
import os.path as op
import typing as t
from io import BytesIO

import pytest
from flask import Flask

from flask_admin import Admin
from flask_admin.contrib import fileadmin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from flask_admin.theme import Bootstrap4Theme


class Base:
    class FileAdminTests:
        _test_files_root = op.join(op.dirname(__file__), "files")

        def fileadmin_class(self) -> type[S3FileAdmin | AzureFileAdmin]:
            raise NotImplementedError

        def fileadmin_args(self) -> tuple[tuple[t.Any, t.Any], dict[t.Any, t.Any]]:
            raise NotImplementedError

        def test_file_admin(
            self, app: Flask, admin: Admin, request: pytest.FixtureRequest
        ) -> None:
            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            def finalizer() -> None:
                try:
                    os.remove(op.join(self._test_files_root, "dummy_renamed.txt"))
                    os.remove(op.join(self._test_files_root, "dummy2.txt"))
                    os.remove(op.join(self._test_files_root, "dummy-pdf.pdf"))
                except OSError:
                    pass

            request.addfinalizer(finalizer)

            class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                editable_extensions = ("txt",)
                allowed_extensions = ("txt",)

            view_kwargs = dict(fileadmin_kwargs)
            view_kwargs.setdefault("name", "Files")
            view = MyFileAdmin(*fileadmin_args, **view_kwargs)

            admin.add_view(view)

            client = app.test_client()

            # index
            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy.txt" in rv.data.decode("utf-8")

            # rename
            rv = client.get("/admin/myfileadmin/rename/?path=dummy.txt")
            assert rv.status_code == 200
            assert "dummy.txt" in rv.data.decode("utf-8")
            assert 'value="dummy.txt"' in rv.data.decode("utf-8")

            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy.txt",
                data=dict(name="dummy_renamed.txt", path="dummy.txt"),
            )
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy_renamed.txt" in rv.data.decode("utf-8")
            assert "path=dummy.txt" not in rv.data.decode("utf-8")

            # upload
            rv = client.get("/admin/myfileadmin/upload/")
            assert rv.status_code == 200

            rv = client.post(
                "/admin/myfileadmin/upload/",
                data=dict(upload=(BytesIO(b""), "dummy.txt")),
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy.txt" in rv.data.decode("utf-8")
            assert "path=dummy_renamed.txt" in rv.data.decode("utf-8")

            # upload existing file
            rv = client.post(
                "/admin/myfileadmin/upload/",
                data=dict(upload=(BytesIO(b""), "dummy.txt")),
                follow_redirects=True,
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert "already exists." in data

            # upload invalid file type
            rv = client.post(
                "/admin/myfileadmin/upload/",
                data=dict(upload=(BytesIO(b""), "dummy-pdf.pdf")),
                follow_redirects=True,
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert "Invalid file type" in data

            # delete
            rv = client.post(
                "/admin/myfileadmin/delete/", data=dict(path="dummy_renamed.txt")
            )
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy_renamed.txt" not in rv.data.decode("utf-8")
            assert "path=dummy.txt" in rv.data.decode("utf-8")

            # mkdir
            rv = client.get("/admin/myfileadmin/mkdir/")
            assert rv.status_code == 200

            rv = client.post("/admin/myfileadmin/mkdir/", data=dict(name="dummy_dir"))
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy.txt" in rv.data.decode("utf-8")
            assert "path=dummy_dir" in rv.data.decode("utf-8")

            # rename - directory
            rv = client.get("/admin/myfileadmin/rename/?path=dummy_dir")
            assert rv.status_code == 200
            assert "dummy_dir" in rv.data.decode("utf-8")

            # rename - directory (modal)
            rv = client.get("/admin/myfileadmin/rename/?path=dummy_dir&modal=1")
            assert rv.status_code == 200
            assert "dummy_dir" in rv.data.decode("utf-8")

            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy_dir",
                data=dict(name="dummy_renamed_dir", path="dummy_dir"),
            )
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy_renamed_dir" in rv.data.decode("utf-8")
            assert "path=dummy_dir" not in rv.data.decode("utf-8")

            # delete - directory
            rv = client.post(
                "/admin/myfileadmin/delete/", data=dict(path="dummy_renamed_dir")
            )
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy_renamed_dir" not in rv.data.decode("utf-8")
            assert "path=dummy.txt" in rv.data.decode("utf-8")

        def test_file_admin_edit(self, app: Flask, admin: Admin) -> None:
            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                editable_extensions = ("txt",)

            view_kwargs = dict(fileadmin_kwargs)
            view_kwargs.setdefault("name", "Files")
            view = MyFileAdmin(*fileadmin_args, **view_kwargs)

            admin.add_view(view)

            client = app.test_client()

            # edit
            rv = client.get("/admin/myfileadmin/edit/?path=dummy.txt")
            assert rv.status_code == 200
            assert "dummy.txt" in rv.data.decode("utf-8")

            rv = client.post(
                "/admin/myfileadmin/edit/?path=dummy.txt",
                data=dict(content="new_string\n"),
            )
            assert rv.status_code == 302

            rv = client.post(
                "/admin/myfileadmin/edit/?path=dummy.txt",
                data=dict(content="new_string 😁\n"),
            )
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/edit/?path=dummy.txt")
            assert rv.status_code == 200
            assert "dummy.txt" in rv.data.decode("utf-8")
            assert "new_string" in rv.data.decode("utf-8")
            assert "😁" in rv.data.decode("utf-8")

        def test_modal_edit_bs4(self, app: Flask, babel: object | None) -> None:
            admin_bs4 = Admin(app, theme=Bootstrap4Theme())

            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class EditModalOn(fileadmin_class):  # type: ignore[valid-type, misc]
                edit_modal = True
                editable_extensions = ("txt",)

            class EditModalOff(fileadmin_class):  # type: ignore[valid-type, misc]
                edit_modal = False
                editable_extensions = ("txt",)

            on_view_kwargs = dict(fileadmin_kwargs)
            on_view_kwargs.setdefault("endpoint", "edit_modal_on")
            edit_modal_on = EditModalOn(*fileadmin_args, **on_view_kwargs)

            off_view_kwargs = dict(fileadmin_kwargs)
            off_view_kwargs.setdefault("endpoint", "edit_modal_off")
            edit_modal_off = EditModalOff(*fileadmin_args, **off_view_kwargs)

            admin_bs4.add_view(edit_modal_on)
            admin_bs4.add_view(edit_modal_off)

            client_bs4 = app.test_client()

            # bootstrap 3 - ensure modal window is added when edit_modal is
            # enabled
            rv = client_bs4.get("/admin/edit_modal_on/")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            assert "fa_modal_window" in data

            # bootstrap 3 - test modal disabled
            rv = client_bs4.get("/admin/edit_modal_off/")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")
            assert "fa_modal_window" not in data

        @pytest.mark.parametrize(
            "url, expected, action_url, post_data, expected_post_res",
            [
                (
                    "/mkdir/?modal=1",
                    [
                        "Create Directory",
                        "modal-header",
                        "modal-body",
                    ],
                    "/admin/mymodalfileadmin/mkdir/",
                    {"name": "dummy_dir"},
                    [
                        "Successfully created directory: dummy_dir",
                        'name="path" type="hidden" value="dummy_dir"',
                    ],
                ),
                (
                    "/upload/?modal=1",
                    [
                        "Upload File",
                        "modal-header",
                        "modal-body",
                    ],
                    "/admin/mymodalfileadmin/upload/",
                    dict(upload=(BytesIO(b""), "dummy3.txt")),
                    [
                        "Successfully saved file: dummy3.txt",
                        'name="path" type="hidden" value="dummy3.txt"',
                    ],
                ),
                (
                    "/edit/?path=dummy.txt&modal=1",
                    [
                        "Editing dummy.txt",
                        "modal-header",
                        "modal-body",
                    ],
                    "/admin/mymodalfileadmin/edit/?path=dummy.txt",
                    {"content": "dummy file 😁\n"},
                    ["Changes to dummy.txt saved successfully"],
                ),
                (
                    "/rename/?path=dummy.txt&modal=1",
                    [
                        "Rename dummy.txt",
                        "modal-header",
                        "modal-body",
                    ],
                    "/admin/mymodalfileadmin/rename/?path=",
                    {"path": "dummy.txt", "name": "dummy_renamed.txt"},
                    [
                        "Successfully renamed",
                        "dummy_renamed.txt",
                        'name="path" type="hidden" value="dummy_renamed.txt"',
                    ],
                ),
            ],
        )
        def test_file_admin_modal(
            self,
            app: Flask,
            admin: Admin,
            url: str,
            expected: list[str],
            action_url: str,
            post_data: dict[str, str],
            expected_post_res: list[str],
            request: pytest.FixtureRequest,
        ) -> None:
            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class MyModalFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                editable_extensions = ("txt",)
                rename_modal = True
                edit_modal = True
                mkdir_modal = True
                upload_modal = True

            view_kwargs = dict(fileadmin_kwargs)
            view_kwargs.setdefault("name", "Files")
            view = MyModalFileAdmin(*fileadmin_args, **view_kwargs)
            admin.add_view(view)

            client = app.test_client()

            def finalizer() -> None:
                restored_file = (BytesIO(b"new_string\n"), "dummy.txt")
                client.post(
                    "/admin/mymodalfileadmin/upload/", data={"upload": restored_file}
                )
                for p in [
                    "dummy_renamed.txt",
                    "dummy3.txt",
                    "dummy_dir",
                    "dummy_renamed_dir",
                ]:
                    client.post("/admin/mymodalfileadmin/delete/", data={"path": p})

            request.addfinalizer(finalizer)

            if fileadmin_class is S3FileAdmin and action_url.startswith(
                "/admin/mymodalfileadmin/edit/"
            ):
                pytest.skip(
                    "Skipping edit tests as S3FileAdmin has no edit file functionality."
                )

            rv = client.get(f"/admin/mymodalfileadmin{url}")
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")

            assert f'action="{action_url}"' in data
            for ex in expected:
                assert ex in data, f"Expected '{ex}' , but it was not found."

            # Ensure any file-like object is reset for this request
            if "upload" in post_data and isinstance(post_data["upload"], tuple):
                _, fname = post_data["upload"]
                post_data["upload"] = (BytesIO(b""), fname)

            rv = client.post(action_url, data=post_data, follow_redirects=True)
            assert rv.status_code == 200
            data = rv.data.decode("utf-8")

            for ex in expected_post_res:
                assert ex in data, f"Expected '{ex}' , but it was not found."


class TestLocalFileAdmin(Base.FileAdminTests):
    def fileadmin_class(self) -> type[FileAdmin]:  # type: ignore[override]
        return fileadmin.FileAdmin

    def fileadmin_args(self) -> tuple[tuple[t.Any, t.Any], dict[t.Any, t.Any]]:
        return (self._test_files_root, "/files"), {}

    def test_fileadmin_sort_bogus_url_param(self, app: Flask, admin: Admin) -> None:
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()
        with open(op.join(self._test_files_root, "dummy2.txt"), "w") as fp:
            # make sure that 'files/dummy2.txt' exists, is newest and has bigger size
            fp.write("test")

            rv = client.get("/admin/myfileadmin/?sort=bogus")
            assert rv.status_code == 200
            assert rv.data.decode("utf-8").find("path=dummy2.txt") < rv.data.decode(
                "utf-8"
            ).find("path=dummy.txt")

            rv = client.get("/admin/myfileadmin/?sort=name")
            assert rv.status_code == 200
            assert rv.data.decode("utf-8").find("path=dummy.txt") < rv.data.decode(
                "utf-8"
            ).find("path=dummy2.txt")
        try:
            # clean up
            os.remove(op.join(self._test_files_root, "dummy2.txt"))
        except OSError:
            pass
