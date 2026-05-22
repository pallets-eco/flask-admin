import typing as t

from flask import Flask
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from wtforms import fields
from wtforms.form import Form

from flask_admin import Admin
from flask_admin import form
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.validators import ItemsRequired
from flask_admin.model.form import InlineFormAdmin
from flask_admin.tests.conftest import skip_or_return_session_or_db
from flask_admin.tests.conftest import T_ANY_SQLA_PROVIDER
from flask_admin.tests.conftest import T_LITERAL_SESSION_OR_DB


def test_inline_form(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

            def __init__(self, name: str | None = None) -> None:
                self.name = name  # type: ignore[assignment]

        class UserInfo(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "user_info"
            id = Column(Integer, primary_key=True)
            key = Column(String, nullable=False)
            val = Column(String)
            user_id = Column(Integer, ForeignKey(User.id))
            user = relationship(
                User,
                backref=backref(
                    "info", cascade="all, delete-orphan", single_parent=True
                ),
            )

        sqla_db_ext.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = (UserInfo,)

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = UserModelView(User, param)
        admin.add_view(view)

        # Basic tests
        assert view._create_form_class is not None
        assert view._edit_form_class is not None
        assert view.endpoint == "user"

        # Verify form
        assert view._create_form_class.name.field_class == fields.StringField  # type: ignore[attr-defined]
        assert view._create_form_class.info.field_class == InlineModelFormList  # type: ignore[attr-defined]

        rv = client.get("/admin/user/")
        assert rv.status_code == 200

        rv = client.get("/admin/user/new/")
        assert rv.status_code == 200

        # Create
        rv = client.post("/admin/user/new/", data=dict(name="äõüxyz"))
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 1
        assert sqla_db_ext.db.session.query(func.count(UserInfo.id)).scalar() == 0

        data: dict[str, str | int | None] = {
            "name": "fbar",
            "info-0-key": "foo",
            "info-0-val": "bar",
        }
        rv = client.post("/admin/user/new/", data=data)
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 2
        assert sqla_db_ext.db.session.query(func.count(UserInfo.id)).scalar() == 1

        # Edit
        rv = client.get("/admin/user/edit/?id=2")
        assert rv.status_code == 200
        # Edit - update
        data = {
            "name": "barfoo",
            "info-0-id": 1,
            "info-0-key": "xxx",
            "info-0-val": "yyy",
        }
        rv = client.post("/admin/user/edit/?id=2", data=data)
        assert sqla_db_ext.db.session.query(func.count(UserInfo.id)).scalar() == 1
        assert sqla_db_ext.db.session.query(UserInfo).one().key == "xxx"

        # Edit - add & delete
        data = {
            "name": "barf",
            "del-info-0": "on",
            "info-0-id": "1",
            "info-0-key": "yyy",
            "info-0-val": "xxx",
            "info-1-id": None,
            "info-1-key": "bar",
            "info-1-val": "foo",
        }
        rv = client.post("/admin/user/edit/?id=2", data=data)
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 2
        user = sqla_db_ext.db.session.get(User, 2)
        assert user and user.name == "barf"
        assert sqla_db_ext.db.session.query(func.count(UserInfo.id)).scalar() == 1
        assert sqla_db_ext.db.session.query(UserInfo).one().key == "bar"

        # Delete
        rv = client.post("/admin/user/delete/?id=2")
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 1
        rv = client.post("/admin/user/delete/?id=1")
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 0
        assert sqla_db_ext.db.session.query(func.count(UserInfo.id)).scalar() == 0


def test_inline_form_required(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[misc,name-defined]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name: str | None = Column(String, unique=True)  # type: ignore[assignment]

            def __init__(self, name: str | None = None) -> None:
                self.name = name

        class UserEmail(sqla_db_ext.Base):  # type: ignore[misc,name-defined]
            __tablename__ = "user_info"
            id = Column(Integer, primary_key=True)
            email = Column(String, nullable=False, unique=True)
            verified_at = Column(DateTime)
            user_id = Column(Integer, ForeignKey(User.id))
            user = relationship(
                User,
                backref=backref(
                    "emails", cascade="all, delete-orphan", single_parent=True
                ),
            )

        sqla_db_ext.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = (UserEmail,)
            form_args = {"emails": {"validators": [ItemsRequired()]}}

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = UserModelView(User, param)
        admin.add_view(view)

        # Create
        rv = client.post("/admin/user/new/", data=dict(name="no-email"))
        assert rv.status_code == 200
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 0

        data = {
            "name": "hasEmail",
            "emails-0-email": "foo@bar.com",
        }
        rv = client.post("/admin/user/new/", data=data)
        assert rv.status_code == 302
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 1
        assert sqla_db_ext.db.session.query(func.count(UserEmail.id)).scalar() == 1

        # Attempted delete, prevented by ItemsRequired
        data = {
            "name": "hasEmail",
            "del-emails-0": "on",
            "emails-0-email": "foo@bar.com",
        }
        rv = client.post("/admin/user/edit/?id=1", data=data)
        assert rv.status_code == 200
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 1
        assert sqla_db_ext.db.session.query(func.count(UserEmail.id)).scalar() == 1


def test_inline_form_ajax_fk(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():
        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name: str | None = Column(String, unique=True)  # type: ignore[assignment]

            def __init__(self, name: str | None = None) -> None:
                self.name = name

        class Tag(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "tags"

            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

        class UserInfo(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "user_info"
            id = Column(Integer, primary_key=True)
            key = Column(String, nullable=False)
            val = Column(String)

            user_id = Column(Integer, ForeignKey(User.id))
            user = relationship(
                User,
                backref=backref(
                    "info", cascade="all, delete-orphan", single_parent=True
                ),
            )

            tag_id = Column(Integer, ForeignKey(Tag.id))
            tag = relationship(Tag, backref="user_info")

        sqla_db_ext.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            opts = {"form_ajax_refs": {"tag": {"fields": ["name"]}}}

            inline_models = [(UserInfo, opts)]  # type: ignore[list-item]

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = UserModelView(User, param)
        admin.add_view(view)

        form = view.create_form()
        user_info_form = form.info.unbound_field.args[0]  # type: ignore[attr-defined]
        loader = user_info_form.tag.args[0]
        assert loader.name == "userinfo-tag"
        assert loader.model == Tag

        assert "userinfo-tag" in view._form_ajax_refs


def test_inline_form_self(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    with app.app_context():

        class Tree(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "tree"
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey("tree.id"))
            parent = relationship("Tree", remote_side=[id], backref="children")

        sqla_db_ext.create_all()

        class TreeView(ModelView):
            inline_models = (Tree,)

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = TreeView(Tree, param)

        parent = Tree()
        child = Tree(parent=parent)
        form = view.edit_form(child)
        assert form.parent.data == parent  # type: ignore[attr-defined]


def test_inline_form_base_class(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    client = app.test_client()

    with app.app_context():
        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name: str | None = Column(String, unique=True)  # type: ignore[assignment]

            def __init__(self, name: str | None = None) -> None:
                self.name = name

        class UserEmail(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "user_info"
            id = Column(Integer, primary_key=True)
            email = Column(String, nullable=False, unique=True)
            verified_at = Column(DateTime)
            user_id = Column(Integer, ForeignKey(User.id))
            user = relationship(
                User,
                backref=backref(
                    "emails", cascade="all, delete-orphan", single_parent=True
                ),
            )

        sqla_db_ext.create_all()

        # Customize error message
        class StubTranslation:
            def gettext(self, *args: t.Any) -> str:
                return "success!"

            def ngettext(self, *args: t.Any) -> str:
                return "success!"

        class StubBaseForm(form.BaseForm):
            class Meta:
                def get_translations(self, form: Form) -> StubTranslation:
                    return StubTranslation()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = ((UserEmail, {"form_base_class": StubBaseForm}),)  # type: ignore[assignment]
            form_args = {"emails": {"validators": [ItemsRequired()]}}

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = UserModelView(User, param)
        admin.add_view(view)

        # Create
        data = {
            "name": "emptyEmail",
            "emails-0-email": "",
        }
        rv = client.post("/admin/user/new/", data=data)
        assert rv.status_code == 200
        assert sqla_db_ext.db.session.query(func.count(User.id)).scalar() == 0
        assert b"success!" in rv.data, rv.data


def test_inline_form_postprocess_form_hook(
    app: Flask,
    sqla_db_ext: T_ANY_SQLA_PROVIDER,
    admin: Admin,
    session_or_db: T_LITERAL_SESSION_OR_DB,
) -> None:
    """``InlineFormAdmin.postprocess_form`` is the hook invoked by the
    inline-model converter to contribute extra fields onto the generated
    inline form class. The matching docstrings in
    ``flask_admin.contrib.sqla.view`` and ``flask_admin.contrib.peewee.view``
    used to advertise a ``post_process`` method on a converter subclass, which
    is never actually invoked anywhere in the codebase -- see issue #1738.

    This test pins the real, working API so the docs cannot drift away from it
    again: subclass ``InlineFormAdmin``, override ``postprocess_form``, pass
    an instance through ``inline_models``, and verify the extra field appears
    on the generated inline form class.
    """
    with app.app_context():
        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

        class UserInfo(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
            __tablename__ = "user_info"
            id = Column(Integer, primary_key=True)
            key = Column(String, nullable=False)
            val = Column(String)
            user_id = Column(Integer, ForeignKey(User.id))
            user = relationship(
                User,
                backref=backref(
                    "info", cascade="all, delete-orphan", single_parent=True
                ),
            )

        sqla_db_ext.create_all()

        class UserInfoInlineForm(InlineFormAdmin):
            def postprocess_form(self, form_class):  # type: ignore[no-untyped-def]
                # Contribute an extra field that does not exist on the SQLA
                # model. If `postprocess_form` is not invoked by the converter,
                # this attribute will be missing on the generated form class.
                form_class.extra = fields.StringField("extra")
                return form_class

        class UserModelView(ModelView):
            inline_models = (UserInfoInlineForm(UserInfo),)

        param = skip_or_return_session_or_db(sqla_db_ext, session_or_db)
        view = UserModelView(User, param)
        admin.add_view(view)

        # On the parent form, the inline relationship lives as an UnboundField
        # whose first positional arg is the generated per-row form class. That
        # class is what `postprocess_form` mutates; assert the contributed
        # field is present on it.
        unbound_info = view._create_form_class.info  # type: ignore[attr-defined]
        inline_form_cls = unbound_info.args[0]
        assert hasattr(inline_form_cls, "extra"), (
            "InlineFormAdmin.postprocess_form should contribute extra fields; "
            "if this fails the converter is no longer calling the hook the "
            "docstrings document."
        )
