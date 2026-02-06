from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from wtforms import fields

from flask_admin import form
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.validators import ItemsRequired


def test_inline_form(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserInfo(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
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

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
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
        assert sqla_db_ext.db.session.get(User, 2).name == "barf"
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


def test_inline_form_required(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserEmail(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
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

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
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


def test_inline_form_ajax_fk(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class Tag(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "tags"

            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

        class UserInfo(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
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

            inline_models = [(UserInfo, opts)]

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = UserModelView(User, param)
        admin.add_view(view)

        form = view.create_form()
        user_info_form = form.info.unbound_field.args[0]  # type: ignore[attr-defined]
        loader = user_info_form.tag.args[0]
        assert loader.name == "userinfo-tag"
        assert loader.model == Tag

        assert "userinfo-tag" in view._form_ajax_refs


def test_inline_form_self(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():

        class Tree(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "tree"
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey("tree.id"))
            parent = relationship("Tree", remote_side=[id], backref="children")

        sqla_db_ext.create_all()

        class TreeView(ModelView):
            inline_models = (Tree,)

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = TreeView(Tree, param)

        parent = Tree()
        child = Tree(parent=parent)
        form = view.edit_form(child)
        assert form.parent.data == parent  # type: ignore[attr-defined]


def test_inline_form_base_class(app, sqla_db_ext, admin, session_or_db):
    client = app.test_client()

    with app.app_context():
        # Set up models and database
        class User(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserEmail(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
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
            def gettext(self, *args):
                return "success!"

            def ngettext(self, *args):
                return "success!"

        class StubBaseForm(form.BaseForm):
            class Meta:
                def get_translations(self, form):
                    return StubTranslation()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = ((UserEmail, {"form_base_class": StubBaseForm}),)
            form_args = {"emails": {"validators": [ItemsRequired()]}}

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
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
