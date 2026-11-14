import os
import os.path as op
import re
import typing as t
from io import BytesIO

import pytest
from flask import Flask
from flask_wtf import CSRFProtect  # type: ignore[import-untyped]

from flask_admin import Admin
from flask_admin.contrib import fileadmin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from flask_admin.form import SecureForm
from flask_admin.theme import Bootstrap4Theme


@pytest.fixture(scope="function", autouse=True)
def initial_files() -> None:
    os.makedirs(op.join(op.dirname(__file__), "files"), exist_ok=True)
    if not op.exists(op.join(op.dirname(__file__), "files", "dummy.txt")):
        with open(op.join(op.dirname(__file__), "files", "dummy.txt"), "w") as fp:
            fp.write("any string")


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
                    os.remove(op.join(self._test_files_root, "dummy.txt"))
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

        def get_csrf_token(self, data: str) -> str:
            pattern = re.compile(
                r'<input[^>]*?name="csrf_token"[^>]*?value="(.*?)".*?>'
            )

            found = pattern.findall(data)
            return found[0] if found else ""

        @pytest.mark.parametrize("csrf_method", ["SecureForm", "CSRFProtect"])
        @pytest.mark.parametrize(
            "page",
            [
                "/admin/fileadmin/",
                "/admin/fileadmin/upload",
                "/admin/fileadmin/rename/?path=dummy.txt",
                "/admin/fileadmin/rename/?path=d1",
                "/admin/fileadmin/mkdir",
                "/admin/fileadmin/edit/?path=dummy.txt",
            ],
        )
        def test_csrf_token(
            self, app: Flask, admin: Admin, page: str, csrf_method: str
        ) -> None:
            # Cross-Site-Request-Forgery (CSRF) Protection
            if csrf_method == "CSRFProtect":
                CSRFProtect(app)

            app.config["WTF_CSRF_ENABLED"] = True

            os.makedirs(op.join(self._test_files_root, "d1"), exist_ok=True)

            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class SecureFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                if csrf_method == "SecureForm":
                    form_base_class = SecureForm
                editable_extensions = ("txt",)

            fileadmin_kwargs["endpoint"] = "fileadmin"
            view = SecureFileAdmin(*fileadmin_args, **fileadmin_kwargs)
            admin.add_view(view)

            client = app.test_client()

            rv = client.get(page, follow_redirects=True)
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert 'name="csrf_token"' in data
            assert len(self.get_csrf_token(data)) >= 5

        @pytest.mark.parametrize("csrf_method", ["SecureForm", "CSRFProtect"])
        def test_csrf_submit(
            self, app: Flask, admin: Admin, request: t.Any, csrf_method: str
        ) -> None:
            # Cross-Site-Request-Forgery (CSRF) Protection
            app.config["WTF_CSRF_ENABLED"] = True

            if csrf_method == "CSRFProtect":
                CSRFProtect(app)

            def finalizer() -> None:
                try:
                    os.remove(op.join(self._test_files_root, "d1/dum.txt"))
                    os.remove(op.join(self._test_files_root, "dummy_renamed.txt"))
                    os.remove(op.join(self._test_files_root, "dummy2.txt"))
                except OSError:
                    pass

            request.addfinalizer(finalizer)

            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class SecureFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                if csrf_method == "SecureForm":
                    form_base_class = SecureForm

                def is_accessible(self) -> bool:
                    return True

            fileadmin_kwargs["endpoint"] = "myfileadmin"
            view = SecureFileAdmin(*fileadmin_args, **fileadmin_kwargs)
            admin.add_view(view)

            client = app.test_client()

            rv = client.get("/admin/myfileadmin/", follow_redirects=True)
            data = rv.data.decode("utf-8")
            # make sure that dummy.txt exists
            assert (
                "dummy.txt" in data
            ), "dummy.txt should be listed on the page to start the test"

            # read the token
            rv = client.get("/admin/myfileadmin", follow_redirects=True)
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert 'name="csrf_token"' in data

            csrf_token = self.get_csrf_token(data)
            assert len(csrf_token) >= 5

            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy.txt",
                data=dict(
                    name="dummy_renamed.txt", path="dummy.txt", csrf_token=csrf_token
                ),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            data = client.get("/admin/myfileadmin/", follow_redirects=True).data.decode(
                "utf-8"
            )
            assert "dummy_renamed.txt" in data

            rv = client.post(
                "/admin/myfileadmin/upload/",
                data=dict(
                    upload=(BytesIO(b""), "dummy_renamed.txt"), csrf_token=csrf_token
                ),
                follow_redirects=True,
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert "dummy_renamed.txt" in client.get(
                "/admin/myfileadmin/", follow_redirects=True
            ).data.decode("utf-8")
            assert "already exists." in data

            # delete
            rv = client.post(
                "/admin/myfileadmin/delete/",
                data=dict(path="dummy_renamed.txt", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert "dummy_renamed.txt" not in client.get(
                "/admin/myfileadmin/", follow_redirects=True
            ).data.decode("utf-8")

            # mkdir
            rv = client.post(
                "/admin/myfileadmin/mkdir/",
                data=dict(name="dummy_dir", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert "dummy_dir" in client.get(
                "/admin/myfileadmin/", follow_redirects=True
            ).data.decode("utf-8")

            # rename - dir
            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy_dir",
                data=dict(
                    name="dummy_renamed_dir", path="dummy_dir", csrf_token=csrf_token
                ),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert "dummy_renamed_dir" in client.get(
                "/admin/myfileadmin/", follow_redirects=True
            ).data.decode("utf-8")

            # delete - directory
            rv = client.post(
                "/admin/myfileadmin/delete/",
                data=dict(path="dummy_renamed_dir", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert "dummy_renamed_dir" not in client.get(
                "/admin/myfileadmin/", follow_redirects=True
            ).data.decode("utf-8")

        @pytest.mark.parametrize("csrf_method", ["SecureForm", "CSRFProtect"])
        def test_csrf_edit(self, app: Flask, admin: Admin, csrf_method: str) -> None:
            # Cross-Site-Request-Forgery (CSRF) Protection
            app.config["WTF_CSRF_ENABLED"] = True

            if csrf_method == "CSRFProtect":
                CSRFProtect(app)

            os.makedirs(op.join(self._test_files_root, "d1"), exist_ok=True)

            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class SecureFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                if csrf_method == "SecureForm":
                    form_base_class = SecureForm

                editable_extensions = ("txt",)  # Enable editing pages

            fileadmin_kwargs["endpoint"] = "fileadmin"
            view = SecureFileAdmin(*fileadmin_args, **fileadmin_kwargs)
            admin.add_view(view)

            client = app.test_client()

            # edit
            rv = client.get("/admin/fileadmin/edit/?path=editable.txt")
            assert rv.status_code == 200
            assert "editable.txt" in rv.data.decode("utf-8")

            csrf_token = self.get_csrf_token(rv.data.decode("utf-8"))
            rv = client.post(
                "/admin/fileadmin/edit/?path=editable.txt",
                data=dict(content="new_string", csrf_token=csrf_token),
            )
            assert rv.status_code == 302

            rv = client.get("/admin/fileadmin/edit/?path=editable.txt")
            assert rv.status_code == 200
            assert "editable.txt" in rv.data.decode("utf-8")
            assert "new_string" in rv.data.decode("utf-8")

            rv = client.post(
                "/admin/fileadmin/edit/?path=editable.txt",
                data=dict(content="new_string"),
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code in [200, 400]
            assert "CSRF token missing" in data or "The CSRF token is missing" in data

        @pytest.mark.parametrize("csrf_method", ["SecureForm", "CSRFProtect"])
        @pytest.mark.parametrize(
            "page, payload",
            [
                ("/admin/myfileadmin/rename/?path=dummy.txt", {}),
                ("/admin/myfileadmin/upload/", {}),
                ("/admin/myfileadmin/delete/", {}),
                ("/admin/myfileadmin/mkdir/", {}),
                ("/admin/myfileadmin/rename/?path=dummy_dir", {}),
                ("/admin/myfileadmin/delete/", {"path": "dummy_renamed_dir"}),
            ],
        )
        def test_csrf_submit_without_token(
            self,
            app: Flask,
            admin: Admin,
            request: t.Any,
            page: str,
            payload: dict[str, t.Any],
            csrf_method: str,
        ) -> None:
            # Cross-Site-Request-Forgery (CSRF) Protection
            app.config["WTF_CSRF_ENABLED"] = True

            expected_msg = "CSRF token missing"
            expected_res_code = 200
            if csrf_method == "CSRFProtect":
                CSRFProtect(app)
                expected_msg = "The CSRF token is missing"
                expected_res_code = 400

            def finalizer() -> None:
                try:
                    os.remove(op.join(self._test_files_root, "d1/dum.txt"))
                    os.remove(op.join(self._test_files_root, "dummy_renamed.txt"))
                    os.remove(op.join(self._test_files_root, "dummy2.txt"))
                except OSError:
                    pass

            request.addfinalizer(finalizer)

            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class SecureFileAdmin(fileadmin_class):  # type: ignore[valid-type, misc]
                if csrf_method == "SecureForm":
                    form_base_class = SecureForm

                def is_accessible(self) -> bool:
                    return True

            fileadmin_kwargs["endpoint"] = "myfileadmin"
            view = SecureFileAdmin(*fileadmin_args, **fileadmin_kwargs)
            admin.add_view(view)

            client = app.test_client()

            pbody = dict(
                name="dummy_renamed.txt", path="dummy.txt", upload=(BytesIO(b""))
            )
            pbody.update(payload)

            rv = client.post(page, data=pbody, follow_redirects=True)
            data = rv.data.decode("utf-8")
            # print(data)
            assert rv.status_code == expected_res_code
            assert expected_msg in data


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
