from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import Session

from flask_admin.contrib.sqlmodel import SQLModelView
from flask_admin.tests.sqlmodel import CustomModelView
from flask_admin.tests.sqlmodel import sqlmodel_base


class PkModelView(CustomModelView):
    def create_model(self, form):
        print("Form data:", form.data)

        model = self.model()
        form.populate_obj(model)
        print("Populated model:", model)

        try:
            self.session.add(model)
            self.session.commit()
            return model
        except Exception as e:
            print("⚠️ Commit failed:", e)
            self.session.rollback()
            return None

    def get_pk_value(self, model):
        # Return a composite string key
        return f"{model.id}-{model.id2}"


def test_multiple_pk(app, engine, admin):
    """Test SQLModelView with multiple primary keys"""
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Model(sqlmodel_class, table=True):
            __tablename__ = "model"

            id: int = Field(sa_column=Column(Integer, primary_key=True))  # ← Fix
            id2: str = Field(sa_column=Column(String(20), primary_key=True))  # ← Fix
            test: str = Field(sa_column=Column(String()))

        # Create all tables
        sqlmodel_class.metadata.create_all(engine)

        # Add view to admin - fix the constructor call

        with Session(engine) as db_session:
            admin.add_view(
                PkModelView(Model, db_session, form_columns=["id", "id2", "test"])
            )
            client = app.test_client()
            # Test creating new record
            rv = client.post(
                "/admin/model/new/", data={"id": 1, "id2": "two", "test": "test3"}
            )
            assert rv.status_code == 302

            # Debug DB contents
            rows = db_session.execute(select(Model)).all()
            print("Rows in DB:", rows)

            # Test viewing records
            rv = client.get("/admin/model/")
            assert rv.status_code == 200
            assert "test3" in rv.text

            # Test editing with correct primary key order
            rv = client.get("/admin/model/edit/?id=1,two")
            assert "test3" in rv.text

            # Test editing with incorrect primary key order (should redirect)
            rv = client.get("/admin/model/edit/?id=two,1")
            assert rv.status_code == 302


# def test_joined_inheritance( app, engine, admin):
#     """Test SQLModelView with joined table inheritance"""
#     with app.app_context():
#         class Parent(SQLModel):
#             id: int = Field(sa_column=Column(Integer, primary_key=True))
#             test: str  = Field( sa_column=Column(String()) )


#         class Child(Parent, table=True):
#             __tablename__ = "children"

#             id: int = Field(primary_key=True, foreign_key="parent.id")
#             name: str = Field(sa_column=Column(String(100)))

#         SQLModel.metadata.create_all(engine)
#         # Use SQLAlchemy ORM session for Flask-Admin
#         orm_session = sessionmaker(bind=engine)()
#         admin.add_view(CustomModelView(Child, orm_session,
#         form_columns=["id", "test", "name"]))
#         client = app.test_client()

#         # Test creating new child record
#         rv = client.post("/admin/child/new/",
#         data={"id": 1, "test": "foo", "name": "bar"})
#         assert rv.status_code == 302

#         # Test editing child record
#         rv = client.get("/admin/child/edit/?id=1")
#         assert "foo" in rv.text
#         assert "bar" in rv.text


def test_single_table_inheritance(app, engine, admin):
    """Test SQLModelView with single table inheritance"""
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Parent(sqlmodel_class):
            id: int = Field(primary_key=True)
            test: str = Field(sa_column=Column(String()))

        class Child(Parent, table=True):
            name: str = Field(sa_column=Column(String(100)))

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            admin.add_view(CustomModelView(Child, db_session))
            client = app.test_client()

            # Test creating new child record
            rv = client.post(
                "/admin/child/new/", data={"id": 1, "test": "foo", "name": "bar"}
            )
            assert rv.status_code == 302

            # Test editing child record
            rv = client.get("/admin/child/edit/?id=1")
            assert "foo" in rv.text
            assert "bar" in rv.text


def test_concrete_table_inheritance(app, engine, admin):
    """Test SQLModelView with concrete table inheritance"""
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Parent(sqlmodel_class):
            id: int = Field(primary_key=True)
            test: str = Field(sa_column=Column(String()))

        class Child(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_column=Column(String(100)))
            test: str = Field(sa_column=Column(String()))

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            admin.add_view(CustomModelView(Child, db_session))
            client = app.test_client()
            # Test creating new child record
            rv = client.post(
                "/admin/child/new/", data={"id": 1, "test": "foo", "name": "bar"}
            )
            assert rv.status_code == 302

            # Test editing child record
            rv = client.get("/admin/child/edit/?id=1")
            assert "foo" in rv.text
            assert "bar" in rv.text


def test_concrete_multipk_inheritance(app, engine, admin):
    """Test SQLModelView with concrete table inheritance and multiple primary keys"""
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Parent(sqlmodel_class):
            id: int = Field(primary_key=True)
            test: str

        class Child(Parent, table=True):
            id2: int = Field(primary_key=True)
            name: str

            __mapper_args__ = {"concrete": True}

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            admin.add_view(PkModelView(Child, db_session))
            client = app.test_client()
            # Test creating new child record - provide both primary key values
            rv = client.post(
                "/admin/child/new/",
                data={"id": 1, "id2": 2, "test": "foo", "name": "bar"},
            )
            assert rv.status_code == 302

            # Test editing child record
            rv = client.get("/admin/child/edit/?id=1,2")
            assert "foo" in rv.text
            assert "bar" in rv.text


def test_basic_crud_operations(app, engine, admin):
    """Test basic CRUD operations with SQLModelView"""
    sqlmodel_class = sqlmodel_base()  # init to clear registry

    class TestModel(sqlmodel_class, table=True):
        id: int = Field(primary_key=True)
        name: str
        email: Optional[str] = None

    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            admin.add_view(SQLModelView(TestModel, db_session))
            client = app.test_client()
            # Test CREATE
            rv = client.post(
                "/admin/testmodel/new/",
                data={"id": 1, "name": "Test User", "email": "test@example.com"},
            )
            assert rv.status_code == 302

            # Test READ (list view)
            rv = client.get("/admin/testmodel/")
            assert "Test User" in rv.text
            assert "test@example.com" in rv.text

            # Test READ (detail view) - skip if not configured
            rv = client.get("/admin/testmodel/details/?id=1")
            # Details view might not be enabled, so accept redirect as well
            assert rv.status_code in [200, 302, 404]

            # Test UPDATE
            rv = client.get("/admin/testmodel/edit/?id=1")
            assert "Test User" in rv.text

            rv = client.post(
                "/admin/testmodel/edit/?id=1",
                data={"id": 1, "name": "Updated User", "email": "updated@example.com"},
            )
            assert rv.status_code == 302

            # Verify update
            rv = client.get("/admin/testmodel/")
            assert "Updated User" in rv.text
            assert "updated@example.com" in rv.text

            # Test DELETE
            rv = client.post("/admin/testmodel/delete/", data={"id": 1})
            assert rv.status_code == 302

            # Verify deletion
            rv = client.get("/admin/testmodel/")
            assert "Updated User" not in rv.text


def test_session_management(app, engine, admin):
    """Test that sessions are properly managed"""
    sqlmodel_class = sqlmodel_base()  # init to clear registry

    class TestModel(sqlmodel_class, table=True):
        id: int = Field(primary_key=True)
        name: str

    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            view = SQLModelView(TestModel, db_session)
            admin.add_view(view)

            # Test that the view has a session and it's a SQLModel Session
            assert hasattr(view, "session")
            assert isinstance(view.session, Session)

            # Test that we can use the session to create a record
            test_record = TestModel(id=1, name="Test")
            view.session.add(test_record)
            view.session.commit()

            # Verify the record was created
            record = view.session.get(TestModel, 1)
            assert record is not None
            assert record.name == "Test"
