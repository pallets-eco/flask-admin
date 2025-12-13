import os.path as op
import secrets

import pytest
from bs4 import BeautifulSoup
from flask_admin import Admin
from flask_admin.contrib import fileadmin
from flask_admin.contrib.sqla.view import ModelView
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def nonce():
    return secrets.token_urlsafe(32)


@pytest.fixture
def admin(app, babel, nonce):
    def csp_nonce_generator():
        return nonce

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin


def test_csp_nonces_injected(app, admin, nonce):
    client = app.test_client()
    rv = client.get("/admin/")
    assert rv.status_code == 200

    soup = BeautifulSoup(rv.data, "html.parser")

    scripts = soup.select("script")
    assert len(scripts) == 9
    for tag in scripts:
        assert tag.attrs["nonce"] == nonce

    styles = soup.select("style")
    assert len(styles) == 0
    for tag in styles:
        assert tag.attrs["nonce"] == nonce


@pytest.fixture
def db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
    # app.config["SQLALCHEMY_ECHO"] = True
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    yield db

    with app.app_context():
        db.session.close()
        db.engine.dispose()


@pytest.fixture
def Model1(app, db):
    class Model1(db.Model):  # type: ignore[name-defined, misc]
        def __init__(
            self,
            test1=None,
            test2=None,
            bool_field=False,
        ):
            self.test1 = test1
            self.test2 = test2
            self.bool_field = bool_field

        id = db.Column(db.Integer, primary_key=True)
        test1 = db.Column(db.String(20))
        test2 = db.Column(db.Unicode(20))
        bool_field = db.Column(db.Boolean)

        def __unicode__(self):
            return self.test1

        def __str__(self):
            return self.test1

    with app.app_context():
        db.create_all()

    return Model1


def fill_db(db, Model1):
    objs = [
        {"test1": "test1_val_1", "test2": "test2_val_1", "bool_field": True},
        {"test1": "test1_val_2", "test2": "test2_val_2", "bool_field": False},
        {"test1": "test1_val_3", "test2": "test2_val_3"},
        {"test1": "test1_val_4", "test2": "test2_val_4"},
    ]

    db.session.add_all([Model1(**obj) for obj in objs])
    db.session.commit()


class TestCSPOnAllPages:
    @pytest.fixture
    def myview(self, app, admin, db, Model1):
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

        with app.app_context():
            fill_db(db, Model1)
            myview = MyModelView(Model1, db.session)
            admin.add_view(myview)

            return myview

    @pytest.fixture
    def modalview(self, app, admin, db, Model1):
        class ModalModelView(ModelView):
            can_create = True
            can_edit = True
            can_delete = True
            column_filters = ["bool_field"]
            column_editable_list = ["test1", "bool_field"]
            column_searchable_list = ["test1", "test2"]
            can_view_details = True
            can_export = True
            page_size_options = (2, 5, 10)

        with app.app_context():
            fill_db(db, Model1)
            vi = ModalModelView(Model1, db.session, endpoint="modal")
            admin.add_view(vi)

            return vi

    _test_files_root = op.join(op.dirname(__file__), "files")

    def fileadmin_class(self):
        return fileadmin.FileAdmin

    def fileadmin_args(self):
        return (self._test_files_root, "/files"), {}

    @pytest.fixture
    def myfileview(self, app, admin):
        fa_class = self.fileadmin_class()
        fa_args, fa_kwargs = self.fileadmin_args()

        class MyFileView(fa_class):  # type: ignore[valid-type, misc]
            can_delete = True
            can_upload = True
            can_delete_dirs = True
            can_rename = True
            editable_extensions = ("txt",)

        vi_kwargs = dict(fa_kwargs)
        vi_kwargs["endpoint"] = "fa"
        vi_kwargs.setdefault("name", "Files")
        vi = MyFileView(*fa_args, **vi_kwargs)

        # files_root = op.join(op.dirname(__file__), "files")
        vi = MyFileView(*fa_args, **vi_kwargs)
        admin.add_view(vi)
        return vi

    @pytest.fixture
    def modalfileview(self, app, admin):
        fa_class = self.fileadmin_class()
        fa_args, fa_kwargs = self.fileadmin_args()

        class ModalFileView(fa_class):  # type: ignore[valid-type, misc]
            can_delete = True
            can_upload = True
            can_delete_dirs = True
            can_rename = True
            edit_modal = True
            rename_modal = True
            mkdir_modal = True
            upload_modal = True
            editable_extensions = ("txt",)

        vi_kwargs = dict(fa_kwargs)
        vi_kwargs.setdefault("name", "ModalFiles")
        vi_kwargs["endpoint"] = "modalfa"
        vi = ModalFileView(*fa_args, **vi_kwargs)

        # files_root = op.join(op.dirname(__file__), "files")

        # vi = ModalFileView(base_path=files_root, endpoint="modalfa")
        admin.add_view(vi)
        return vi

    @pytest.mark.parametrize(
        "name, endpoint, url",
        [
            (
                "Model1 List",
                "model1",
                "?flt1_0=1",
            ),
            (
                "Model1 Create",
                "model1",
                "new/",
            ),
            (
                "Model1 Edit",
                "model1",
                "edit/?id=1",
            ),
            (
                "Model1 Details",
                "model1",
                "details/?id=1",
            ),
            (
                "Modal List",
                "modal",
                "?flt1_0=1",
            ),
            (
                "Modal Create",
                "modal",
                "new/",
            ),
            (
                "Modal Edit",
                "modal",
                "edit/?id=1",
            ),
            (
                "Modal Details",
                "modal",
                "details/?id=1",
            ),
            (
                "FileAdmin List",
                "fa",
                "",
            ),
            (
                "FileAdmin rename",
                "fa",
                "rename/?path=test.txt",
            ),
            (
                "FileAdmin rename dir",
                "fa",
                "rename/?path=dir1",
            ),
            (
                "FileAdmin edit",
                "fa",
                "edit/?path=test.txt",
            ),
            (
                "ModalFileAdmin List",
                "modalfa",
                "",
            ),
            (
                "ModalFileAdmin rename",
                "modalfa",
                "rename/?path=test.txt",
            ),
            (
                "ModalFileAdmin rename dir",
                "modalfa",
                "rename/?path=dir1",
            ),
            (
                "ModalFileAdmin edit",
                "modalfa",
                "edit/?path=test.txt",
            ),
        ],
    )
    def test_csp(
        self,
        app,
        myview,
        modalview,
        myfileview,
        modalfileview,
        nonce,
        name,
        endpoint,
        url,
    ):
        with app.app_context():
            client = app.test_client()

            # check that we can retrieve a list view
            rv = client.get(f"/admin/{endpoint}/{url}")
            assert rv.status_code == 200

            soup = BeautifulSoup(rv.data, "html.parser")

            scripts = soup.select("script")
            for tag in scripts:
                assert tag.attrs["nonce"] == nonce

            styles = soup.select("style")
            for tag in styles:
                assert tag.attrs["nonce"] == nonce
