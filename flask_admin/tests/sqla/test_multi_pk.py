import typing as t

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from .test_basic import CustomModelView


def test_multiple_pk(app, sqla_db_ext, admin, session_or_db):
    # Test multiple primary keys - mix int and string together
    with app.app_context():

        class Model(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "model"
            id = Column(Integer, primary_key=True)
            id2 = Column(String(20), primary_key=True)
            test = Column(String)

        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Model, param, form_columns=["id", "id2", "test"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model/")
        assert rv.status_code == 200

        rv = client.post("/admin/model/new/", data=dict(id=1, id2="two", test="test3"))
        assert rv.status_code == 302

        rv = client.get("/admin/model/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test3" in data

        rv = client.get("/admin/model/edit/?id=1,two")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test3" in data

        # Correct order is mandatory -> fail here
        rv = client.get("/admin/model/edit/?id=two,1")
        assert rv.status_code == 302


def test_joined_inheritance(app, sqla_db_ext, admin, session_or_db):
    # Test multiple primary keys - mix int and string together
    with app.app_context():

        class Parent(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "parent"
            id = Column(Integer, primary_key=True)
            test = Column(String)

            discriminator = Column("type", String(50))
            __mapper_args__ = {"polymorphic_on": discriminator}

        class Child(Parent):
            __tablename__ = "children"
            __mapper_args__: dict[str, t.Any] = {"polymorphic_identity": "child"}

            id = Column(ForeignKey(Parent.id), primary_key=True)
            name = Column(String(100))

        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Child, param, form_columns=["id", "test", "name"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/child/")
        assert rv.status_code == 200

        rv = client.post("/admin/child/new/", data=dict(id=1, test="foo", name="bar"))
        assert rv.status_code == 302

        rv = client.get("/admin/child/edit/?id=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "foo" in data
        assert "bar" in data


def test_single_table_inheritance(app, sqla_db_ext, admin, session_or_db):
    class Parent(sqla_db_ext.Base):  # type: ignore[misc, name-defined]
        __tablename__ = "parent"

        id = Column(Integer, primary_key=True)
        test = Column(String)

        discriminator = Column("type", String(50))
        __mapper_args__ = {"polymorphic_on": discriminator}

    class Child(Parent):
        __mapper_args__: dict[str, t.Any] = {"polymorphic_identity": "child"}
        name = Column(String(100))

    sqla_db_ext.create_all()

    param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
    view = CustomModelView(Child, param, form_columns=["id", "test", "name"])
    admin.add_view(view)

    client = app.test_client()

    rv = client.get("/admin/child/")
    assert rv.status_code == 200

    rv = client.post("/admin/child/new/", data=dict(id=1, test="foo", name="bar"))
    assert rv.status_code == 302

    rv = client.get("/admin/child/edit/?id=1")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "foo" in data
    assert "bar" in data


def test_concrete_table_inheritance(app, sqla_db_ext, admin, session_or_db):
    # Test multiple primary keys - mix int and string together
    with app.app_context():

        class Parent(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "parent"
            id = Column(Integer, primary_key=True)
            test = Column(String)

        class Child(Parent):
            __mapper_args__ = {"concrete": True}
            name = Column(String(100))

        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Child, param, form_columns=["id", "test", "name"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/child/")
        assert rv.status_code == 200

        rv = client.post("/admin/child/new/", data=dict(id=1, test="foo", name="bar"))
        assert rv.status_code == 302

        rv = client.get("/admin/child/edit/?id=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "foo" in data
        assert "bar" in data


def test_concrete_multipk_inheritance(app, sqla_db_ext, admin, session_or_db):
    # Test multiple primary keys - mix int and string together
    with app.app_context():

        class Parent(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "parent"
            id = Column(Integer, primary_key=True)
            test = Column(String)

        class Child(Parent):
            __tablename__ = "child_concrete"
            __mapper_args__ = {
                "concrete": True,
                # NOT involve the parent in queries for the child
                "polymorphic_identity": "child",
            }
            id = Column(Integer, primary_key=True)
            id2 = Column(Integer, primary_key=True)
            test = Column(String)
            name = Column(String(100))

        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Child, param, form_columns=["id", "id2", "test", "name"])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/child/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/child/new/", data=dict(id=1, id2=2, test="foo", name="bar")
        )
        assert rv.status_code == 302

        rv = client.get("/admin/child/edit/?id=1,2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "foo" in data
        assert "bar" in data
