import os.path as op

import pytest
import sqlalchemy as sa
from bs4 import BeautifulSoup
from flask_admin.contrib import fileadmin
from flask_admin.contrib.sqla.view import ModelView


def create_model_class(sqla_db_ext):
    class Model1(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "model1"

        def __init__(
            self,
            test1=None,
            test2=None,
            bool_field=False,
        ):
            self.test1 = test1
            self.test2 = test2
            self.bool_field = bool_field

        id = sa.Column(sa.Integer, primary_key=True)
        test1 = sa.Column(sa.String(20))
        test2 = sa.Column(sa.Unicode(20))
        bool_field = sa.Column(sa.Boolean)

            return self.test1

        def __str__(self):
            return self.test1

    # with app.app_context():
    sqla_db_ext.create_all()

    return Model1


def fill_db(sqla_db_ext, session_or_db, Model1):
    objs = [
        {"test1": "test1_val_1", "test2": "test2_val_1", "bool_field": True},
        {"test1": "test1_val_2", "test2": "test2_val_2", "bool_field": False},
        {"test1": "test1_val_3", "test2": "test2_val_3"},
        {"test1": "test1_val_4", "test2": "test2_val_4"},
    ]

    sqla_db_ext.db.session.add_all([Model1(**obj) for obj in objs])
    sqla_db_ext.db.session.commit()


class MyModelView(ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    column_filters = ["bool_field"]
    column_editable_list = ["test1", "bool_field"]
    column_searchable_list = ["test1", "test2"]
    can_view_details = True
    can_export = True
    page_size_options = (2, 5, 10)


class MyFileView(fileadmin.FileAdmin):
    can_delete = True
    can_upload = True
    can_delete_dirs = True
    can_rename = True
    editable_extensions = ("txt",)


class TestCSPOnAllPages:
    def create_modelview(self, app, admin, db_param, Model1):
        with app.app_context():
            v = MyModelView(Model1, db_param)
            admin.add_view(v)

            return v

    def create_modelveiw_with_modal(self, app, admin, db_param, Model1):
        class ModalModelView(MyModelView):
            create_modal = True
            edit_modal = True
            details_modal = True

        with app.app_context():
            vi = ModalModelView(Model1, db_param, endpoint="modal")
            admin.add_view(vi)

            return vi

    _test_files_root = op.join(op.dirname(__file__), "files")

    def create_fileview(self, admin):
        view = MyFileView(self._test_files_root, name="Files", endpoint="fa")
        admin.add_view(view)

        return view

    def create_fileview_with_modal(self, admin):
        class ModalFileView(MyFileView):
            edit_modal = True
            rename_modal = True
            mkdir_modal = True
            upload_modal = True

        v = ModalFileView(self._test_files_root, name="ModalFiles", endpoint="modalfa")

        admin.add_view(v)
        return v

    @pytest.mark.parametrize(
        "endpoint, url",
        [
            ("", ""),  # index view
            ("model1", "?flt1_0=1"),
            ("model1", "new/"),
            ("model1", "edit/?id=1"),
            ("model1", "details/?id=1"),
            ("modal", "?flt1_0=1"),
            ("modal", "new/"),
            ("modal", "edit/?id=1"),
            ("modal", "details/?id=1"),
            ("fa", ""),
            ("fa", "rename/?path=test.txt"),
            ("fa", "rename/?path=dir1"),
            ("fa", "edit/?path=test.txt"),
            ("modalfa", ""),
            ("modalfa", "rename/?path=test.txt"),
            ("modalfa", "rename/?path=dir1"),
            ("modalfa", "edit/?path=test.txt"),
        ],
    )
    def test_csp(
        self,
        app,
        admin,
        sqla_db_ext,
        session_or_db,
        nonce,
        endpoint,
        url,
    ):
        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        Model1 = create_model_class(sqla_db_ext)

        self.create_modelview(app, admin, param, Model1)
        self.create_modelveiw_with_modal(app, admin, param, Model1)
        self.create_fileview(admin)
        self.create_fileview_with_modal(admin)

        with app.app_context():
            fill_db(sqla_db_ext, sqla_db_ext, Model1)
            client = app.test_client()

        # check that we can retrieve a list view
        rv = client.get(f"/admin/{endpoint}/{url}", follow_redirects=True)
        assert rv.status_code == 200

        soup = BeautifulSoup(rv.data, "html.parser")

        scripts = soup.select("script")
        for tag in scripts:
            assert tag.attrs["nonce"] == nonce

        styles = soup.select("style")
        for tag in styles:
            assert tag.attrs["nonce"] == nonce

    # FIXME: This test is currently a no-op since the RedisView is not being added
    # to the admin instance. We should add it and then test that the nonce is
    # injected into the view's templates.
    @pytest.mark.skip(reason="RedisView is not added to the admin instance.")
    def test_csp_on_rediscli(self, app, admin, nonce):
        pass
