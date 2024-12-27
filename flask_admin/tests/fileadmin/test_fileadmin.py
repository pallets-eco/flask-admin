import os
import os.path as op
from io import BytesIO

from flask_admin import Admin
from flask_admin.contrib import fileadmin
from flask_admin.theme import Bootstrap4Theme


class Base:
    class FileAdminTests:
        _test_files_root = op.join(op.dirname(__file__), "files")

        def fileadmin_class(self):
            raise NotImplementedError

        def fileadmin_args(self):
            raise NotImplementedError

        def test_file_admin(self, app, admin):
            fileadmin_class = self.fileadmin_class()
            fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

            class MyFileAdmin(fileadmin_class):
                editable_extensions = ("txt",)

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
            assert rv.status_code == 302

            rv = client.get("/admin/myfileadmin/")
            assert rv.status_code == 200
            assert "path=dummy.txt" in rv.data.decode("utf-8")
            assert "path=dummy_renamed.txt" in rv.data.decode("utf-8")

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

            class MyFileAdmin(fileadmin_class):
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
                data=dict(content="new_string"),
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

            class EditModalOn(fileadmin_class):
                edit_modal = True
                editable_extensions = ("txt",)

            class EditModalOff(fileadmin_class):
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


class TestLocalFileAdmin(Base.FileAdminTests):
    def fileadmin_class(self):
        return fileadmin.FileAdmin

    def fileadmin_args(self):
        return (self._test_files_root, "/files"), {}

    def test_fileadmin_sort_bogus_url_param(self, app, admin):
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):
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
