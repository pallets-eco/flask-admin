import typing as t

import pytest
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

if t.TYPE_CHECKING:
    Field = t.cast(t.Any, None)
    SQLModel = t.cast(t.Any, None)
    create_engine = t.cast(t.Any, None)
    User = t.Any
else:
    try:
        from sqlmodel import create_engine
        from sqlmodel import Field
        from sqlmodel import SQLModel
    except ImportError as exc:
        pytest.skip(f"sqlmodel backend unavailable: {exc}", allow_module_level=True)

    class User(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        name: str


from flask_admin.contrib.sqlmodel import ModelView


@pytest.fixture
def sqlmodel_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    session = scoped_session(
        sessionmaker(bind=engine, autoflush=False, autocommit=False)
    )
    try:
        yield session
    finally:
        session.remove()
        SQLModel.metadata.drop_all(engine)


def test_modelview_crud(app, admin, sqlmodel_session):
    view = ModelView(t.cast(type[t.Any], User), sqlmodel_session)
    admin.add_view(view)

    client = app.test_client()

    rv = client.get("/admin/user/")
    assert rv.status_code == 200

    rv = client.get("/admin/user/new/")
    assert rv.status_code == 200

    rv = client.post("/admin/user/new/", data={"name": "alice"})
    assert rv.status_code == 302

    rv = client.get("/admin/user/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "alice" in data

    model = sqlmodel_session.query(User).first()
    assert model is not None

    rv = client.post(f"/admin/user/edit/?id={model.id}", data={"name": "bob"})
    assert rv.status_code == 302

    rv = client.get("/admin/user/")
    data = rv.data.decode("utf-8")
    assert "bob" in data

    rv = client.post(f"/admin/user/delete/?id={model.id}")
    assert rv.status_code == 302
    assert sqlmodel_session.query(User).count() == 0
