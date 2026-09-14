import os.path as op
import typing as t

import pytest
import sqlalchemy as sa
from bs4 import BeautifulSoup
from flask import Flask
from flask_admin._types import T_SQLALCHEMY_MODEL
from flask_admin.base import Admin
from flask_admin.contrib import fileadmin
from flask_admin.contrib.sqla.view import ModelView
from flask_admin.tests.conftest import skip_or_return_session_or_db
from flask_admin.tests.conftest import T_ANY_SQLA_PROVIDER
from flask_admin.tests.conftest import T_LITERAL_SESSION_OR_DB


def create_model_class(sqla_db_ext: T_ANY_SQLA_PROVIDER) -> T_SQLALCHEMY_MODEL:
    class Model1(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
        __tablename__ = "model1"

        id = sa.Column(sa.Integer, primary_key=True)
        test1 = sa.Column(sa.String(20))
        test2 = sa.Column(sa.Unicode(20))
        bool_field = sa.Column(sa.Boolean)

    sqla_db_ext.create_all()

    return Model1


def fill_db(sqla_db_ext: T_ANY_SQLA_PROVIDER, Model1: t.Any) -> None:
    objs: list[dict[str, t.Any]] = [
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
    def create_modelview(
        self, app: Flask, admin: Admin, db_session: t.Any, Model1: t.Any
    ) -> MyModelView:
        with app.app_context():
            v = MyModelView(Model1, db_session)
            admin.add_view(v)

            return v

    def create_modelview_with_modal(
        self, app: Flask, admin: Admin, db_session: t.Any, Model1: t.Any
    ) -> MyModelView:
        class ModalModelView(MyModelView):
            create_modal = True
            edit_modal = True
            details_modal = True

        with app.app_context():
            vi = ModalModelView(Model1, db_session, endpoint="modal")
            admin.add_view(vi)

            return vi

    _test_files_root = op.join(op.dirname(__file__), "files")

    def create_fileview(self, admin: Admin) -> MyFileView:
        view = MyFileView(self._test_files_root, name="Files", endpoint="fa")
        admin.add_view(view)

        return view

    def create_fileview_with_modal(self, admin: Admin) -> MyFileView:
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
        app: Flask,
        admin: Admin,
        sqla_db_ext: T_ANY_SQLA_PROVIDER,
        session_or_db: T_LITERAL_SESSION_OR_DB,
        nonce: str,
        endpoint: str,
        url: str,
    ) -> None:
        Model1 = create_model_class(sqla_db_ext)

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        self.create_modelview(app, admin, param, Model1)
        self.create_modelview_with_modal(app, admin, param, Model1)
        self.create_fileview(admin)
        self.create_fileview_with_modal(admin)

        with app.app_context():
            fill_db(sqla_db_ext, Model1)
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
    def test_csp_on_rediscli(self, app: Flask, admin: Admin, nonce: str) -> None:
        pass
