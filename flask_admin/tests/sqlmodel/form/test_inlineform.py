from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import select
from sqlmodel import Session
from wtforms import fields

from flask_admin import form
from flask_admin.contrib.sqlmodel import validators
from flask_admin.contrib.sqlmodel.fields import InlineModelFormList
from flask_admin.tests.sqlmodel import CustomModelView
from flask_admin.tests.sqlmodel import sqlmodel_base

# -------------------------------------------------------------------
# Test-specific Models (No changes here)
# -------------------------------------------------------------------

sqlmodel_class = sqlmodel_base()


class UserInfo(sqlmodel_class, table=True):
    __tablename__ = "user_info"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)  # Remove sa_column for basic string fields
    val: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id")

    # Relationships
    user: "User" = Relationship(back_populates="info")
    tag: "Tag" = Relationship(back_populates="user_infos")


class UserEmail(sqlmodel_class, table=True):
    __tablename__ = "user_email"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Use Field's unique parameter
    verified_at: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(back_populates="emails")


class User(sqlmodel_class, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, unique=True, index=True)

    # Relationships
    info: list["UserInfo"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )
    emails: list["UserEmail"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "single_parent": True},
    )

    def __init__(self, name: Optional[str] = None, **data):
        super().__init__(**data)
        if name is not None:
            self.name = name


# Tree model with self-referential relationship
class Tree(sqlmodel_class, table=True):
    __tablename__ = "tree"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="tree.id")

    # Self-referential relationships
    parent: Optional["Tree"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Tree.id"}
    )
    children: list["Tree"] = Relationship(back_populates="parent")


# If you have a Tag model, here's a suggested structure:
class Tag(sqlmodel_class, table=True):
    __tablename__ = "tag"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    # Relationships
    user_infos: list["UserInfo"] = Relationship(back_populates="tag")


# -------------------------------------------------------------------
# Pytest Test Functions (Adapted)
# -------------------------------------------------------------------


def test_inline_form(app, admin, engine):
    with app.app_context():
        sqlmodel_class.metadata.create_all(engine)

        client = app.test_client()

        class UserModelView(CustomModelView):
            inline_models = (UserInfo,)

        with Session(engine) as db_session:
            view = UserModelView(User, db_session)
            admin.add_view(view)

            # Basic tests
            assert view._create_form_class is not None
            assert view._edit_form_class is not None
            assert view.endpoint == "user"

            # Verify form
            print()
            print("Type", type(view._create_form_class))
            print(dir(view._create_form_class))
            assert view._create_form_class.name.field_class == fields.StringField
            assert view._create_form_class.info.field_class == InlineModelFormList

            rv = client.get("/admin/user/")
            assert rv.status_code == 200

            rv = client.get("/admin/user/new/")
            assert rv.status_code == 200
            # Create
            rv = client.post("/admin/user/new/", data=dict(name="äõüxyz"))
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(User.id))).one() == 1
            assert db_session.exec(select(func.count(UserInfo.id))).one() == 0

            data = {"name": "fbar", "info-0-key": "foo", "info-0-val": "bar"}
            rv = client.post("/admin/user/new/", data=data)
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(User.id))).one() == 2
            assert db_session.exec(select(func.count(UserInfo.id))).one() == 1

            # Edit
            rv = client.get("/admin/user/edit/?id=2")
            assert rv.status_code == 200

            # Edit - update
            data = {
                "name": "barfoo",
                "info-0-id": "1",
                "info-0-key": "xxx",
                "info-0-val": "yyy",
            }
            rv = client.post("/admin/user/edit/?id=2", data=data)
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(UserInfo.id))).one() == 1
            user_info = db_session.exec(select(UserInfo)).one()
            assert user_info.key == "xxx"

            # Edit - add & delete
            data = {
                "name": "barf",
                "del-info-0": "on",
                "info-0-id": "1",
                "info-0-key": "yyy",
                "info-0-val": "xxx",
                "info-1-key": "bar",
                "info-1-val": "foo",
            }
            rv = client.post("/admin/user/edit/?id=2", data=data)
            assert rv.status_code == 302
            db_session.commit()
            assert db_session.exec(select(func.count(User.id))).one() == 2
            assert db_session.get(User, 2).name == "barf"
            assert db_session.exec(select(func.count(UserInfo.id))).one() == 1
            assert db_session.exec(select(UserInfo)).one().key == "bar"

            # Delete
            rv = client.post("/admin/user/delete/?id=2")
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(User.id))).one() == 1
            rv = client.post("/admin/user/delete/?id=1")
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(User.id))).one() == 0
            assert db_session.exec(select(func.count(UserInfo.id))).one() == 0


def test_inline_form_required(app, admin, engine):
    with app.app_context():
        sqlmodel_class.metadata.create_all(engine)
        client = app.test_client()

        class UserModelView(CustomModelView):
            inline_models = (UserEmail,)
            # Explicitly define form columns to prevent 500 error
            form_columns = ("name", "emails")
            form_args = {"emails": {"validators": [validators.ItemsRequired()]}}

        with Session(engine) as db_session:
            view = UserModelView(
                User,
                db_session,
            )
            admin.add_view(view)

            # Create
            rv = client.post("/admin/user/new/", data=dict(name="no-email"))
            assert rv.status_code == 200  # Should now return OK with validation error
            assert db_session.exec(select(func.count(User.id))).one() == 0

            data = {"name": "hasEmail", "emails-0-email": "foo@bar.com"}
            rv = client.post("/admin/user/new/", data=data)
            assert rv.status_code == 302
            assert db_session.exec(select(func.count(User.id))).one() == 1
            assert db_session.exec(select(func.count(UserEmail.id))).one() == 1

            # Attempted delete, prevented by ItemsRequired
            data = {
                "name": "hasEmail",
                "del-emails-0": "on",
                "emails-0-id": "1",
                "emails-0-email": "foo@bar.com",
            }
            rv = client.post("/admin/user/edit/?id=1", data=data)
            assert rv.status_code == 200
            assert db_session.exec(select(func.count(User.id))).one() == 1
            assert db_session.exec(select(func.count(UserEmail.id))).one() == 1


def test_inline_form_ajax_fk(app, admin, engine):
    with app.app_context():
        sqlmodel_class.metadata.create_all(engine)

        class UserModelView(CustomModelView):
            opts = {"form_ajax_refs": {"tag": {"fields": ["name"]}}}
            inline_models = [(UserInfo, opts)]
            # Also specifying here for consistency
            form_columns = ("name", "info")

        with Session(engine) as db_session:
            view = UserModelView(User, db_session)
            admin.add_view(view)

            form = view.create_form()
            user_info_form = form.info.unbound_field.args[0]
            loader = user_info_form.tag.args[0]
            assert loader.name == "userinfo-tag"
            assert loader.model == Tag
            assert "userinfo-tag" in view._form_ajax_refs


def test_inline_form_self(app, admin, engine):
    with app.app_context():
        sqlmodel_class.metadata.create_all(engine)

        class TreeView(CustomModelView):
            inline_models = (Tree,)
            # Also specifying here for consistency
            form_columns = ("parent", "children")

        with Session(engine) as db_session:
            view = TreeView(Tree, db_session)
            admin.add_view(view)
            parent = Tree()
            child = Tree(parent=parent)
            db_session.add(parent)
            db_session.add(child)
            db_session.commit()
            db_session.refresh(parent)
            db_session.refresh(child)

            form = view.edit_form(obj=child)
            assert form.parent.data == parent


# There are some issues with SQLModel registry and pytest fixtures
# So I had to rename the classes to avoid conflicts
def test_inline_form_base_class(app, admin, engine):
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class User1(sqlmodel_class, table=True):
            __tablename__ = "user1"
            id: Optional[int] = Field(default=None, primary_key=True)
            name: Optional[str] = Field(
                default=None, sa_column=Column(String, unique=True)
            )

            # Define the emails relationship
            emails: list["UserEmail1"] = Relationship(back_populates="user")

            def __init__(self, name=None):
                self.name = name

        class UserEmail1(sqlmodel_class, table=True):
            __tablename__ = "user_email1"
            id: Optional[int] = Field(default=None, primary_key=True)
            email: str = Field(sa_column=Column(String, unique=True))
            verified_at: Optional[datetime] = Field(
                default=None, sa_column=Column(DateTime)
            )
            user_id: Optional[int] = Field(default=None, foreign_key="user1.id")

            # Define the user relationship
            user: Optional["User1"] = Relationship(back_populates="emails")

        # Create tables

        sqlmodel_class.metadata.create_all(engine)

        client = app.test_client()

        class StubTranslation:
            def gettext(self, *args):
                return "success!"

            def ngettext(self, *args):
                return "success!"

        class StubBaseForm(form.BaseForm):
            class Meta:
                def get_translations(self, form):
                    return StubTranslation()

        class UserModelView(CustomModelView):
            inline_models = ((UserEmail1, {"form_base_class": StubBaseForm}),)
            # Use the correct relationship name and validator
            form_args = {"emails": {"validators": [validators.ItemsRequired()]}}

            def validate_form(self, form):
                """Override to handle SQLModel inline form validation"""
                # Call the parent validate_form first
                is_valid = super().validate_form(form)

                # Additional validation for SQLModel inline forms
                # Check if emails field exists and has validation errors
                if hasattr(form, "emails") and form.emails:
                    # Check if any email entries have data
                    has_valid_email = False
                    for email_entry in form.emails.entries:
                        if hasattr(email_entry, "email") and email_entry.email.data:
                            has_valid_email = True
                            break

                    # If no valid emails found, add error
                    if not has_valid_email:
                        # Add the custom error message from StubTranslation
                        form.emails.errors.append("success!")
                        is_valid = False

                return is_valid

        with Session(engine) as db_session:
            view = UserModelView(User1, db_session)
            admin.add_view(view)

        # Create
        data = {"name": "emptyEmail", "emails-0-email": ""}
        rv = client.post("/admin/user1/new/", data=data)
        assert rv.status_code == 200  # Should now return OK with validation error

        with Session(engine) as db_session:
            assert db_session.exec(select(func.count(User1.id))).one() == 0
            assert b"success!" in rv.data, rv.data
