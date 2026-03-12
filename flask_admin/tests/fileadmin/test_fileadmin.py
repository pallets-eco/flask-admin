import os
import os.path as op
from io import BytesIO

import pytest

from flask_admin import Admin
from flask_admin.contrib import fileadmin
from flask_admin.form import SecureForm
from flask_admin.theme import Bootstrap4Theme


class SecureFileAdmin(fileadmin.FileAdmin):
    form_base_class = SecureForm

    def is_accessible(self):
        return True


class Base:
    class FileAdminTests:
        _test_files_root = op.join(op.dirname(__file__), "files")

        def fileadmin_class(self):
            raise NotImplementedError

        def fileadmin_args(self):
            raise NotImplementedError

        def test_file_admin(self, app, admin, request):
            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            def finalizer():
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

        def test_file_admin_edit(self, app, admin):
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

            rv = client.get("/admin/myfileadmin/edit/?path=dummy.txt")
            assert rv.status_code == 200
            assert "dummy.txt" in rv.data.decode("utf-8")
            assert "new_string" in rv.data.decode("utf-8")

        def test_modal_edit_bs4(self, app, babel):
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

        def get_csrf_token(self, data):
            data = data.split('name="csrf_token" type="hidden" value="')[1]
            token = data.split('"')[0]
            return token

        @pytest.mark.parametrize(
            "page",
            [
                "/admin/fileadmin/",
                "/admin/fileadmin/upload",
                "/admin/fileadmin/rename/?path=dummy.txt",
                "/admin/fileadmin/rename/?path=d1",
                "/admin/fileadmin/mkdir",
            ],
        )
        def test_csrf_token(self, app, admin, page):
            # Cross-Site-Request-Forgery (CSRF) Protection
            app.config["WTF_CSRF_ENABLED"] = True

            view = SecureFileAdmin(
                self._test_files_root, "/files", endpoint="fileadmin"
            )
            admin.add_view(view)

            client = app.test_client()

            rv = client.get(page, follow_redirects=True)
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert 'name="csrf_token"' in data
            assert len(self.get_csrf_token(data)) == 56

        def test_csrf_submit(self, app, admin):
            # Cross-Site-Request-Forgery (CSRF) Protection
            app.config["WTF_CSRF_ENABLED"] = True

            view = SecureFileAdmin(
                self._test_files_root, "/files", endpoint="myfileadmin"
            )
            admin.add_view(view)

            client = app.test_client()

            assert os.path.exists(op.join(self._test_files_root, "dummy.txt"))

            # read the token
            rv = client.get("/admin/myfileadmin", follow_redirects=True)
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert 'name="csrf_token"' in data
            assert len(self.get_csrf_token(data)) == 56
            csrf_token = self.get_csrf_token(data)

            # rename
            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy.txt",
                data=dict(
                    name="dummy_renamed.txt",
                    path="dummy.txt",
                ),
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert "CSRF token missing." in data

            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy.txt",
                data=dict(
                    name="dummy_renamed.txt", path="dummy.txt", csrf_token=csrf_token
                ),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert os.path.exists(op.join(self._test_files_root, "dummy_renamed.txt"))

            rv = client.post(
                "/admin/myfileadmin/upload/",
                data=dict(upload=(BytesIO(b""), "dummy.txt"), csrf_token=csrf_token),
                follow_redirects=True,
            )
            data = rv.data.decode("utf-8")
            assert rv.status_code == 200
            assert os.path.exists(op.join(self._test_files_root, "dummy.txt"))
            assert "already exists." in data

            # delete
            rv = client.post(
                "/admin/myfileadmin/delete/",
                data=dict(path="dummy_renamed.txt", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert not os.path.exists(
                op.join(self._test_files_root, "dummy_renamed.txt")
            )

            # mkdir
            rv = client.post(
                "/admin/myfileadmin/mkdir/",
                data=dict(name="dummy_dir", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert os.path.exists(op.join(self._test_files_root, "dummy_dir"))

            # rename - dir
            rv = client.post(
                "/admin/myfileadmin/rename/?path=dummy_dir",
                data=dict(
                    name="dummy_renamed_dir", path="dummy_dir", csrf_token=csrf_token
                ),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert os.path.exists(op.join(self._test_files_root, "dummy_renamed_dir"))

            # delete - directory
            rv = client.post(
                "/admin/myfileadmin/delete/",
                data=dict(path="dummy_renamed_dir", csrf_token=csrf_token),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert not os.path.exists(
                op.join(self._test_files_root, "dummy_renamed_dir")
            )


class TestLocalFileAdmin(Base.FileAdminTests):
    def fileadmin_class(self):
        return fileadmin.FileAdmin

    def fileadmin_args(self):
        return (self._test_files_root, "/files"), {}

    def test_fileadmin_sort_bogus_url_param(self, app, admin):
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
