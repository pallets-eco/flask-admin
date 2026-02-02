import pytest
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from flask_admin.contrib.sqla.view import ModelView

# @pytest.fixture
# def admin(app):

#     admin = Admin(
#       app,
#       html_safe_policy=None)

#     yield admin


@pytest.fixture
def db(app):
    with app.app_context():
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
        app.config["SQLALCHEMY_ECHO"] = True
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db = SQLAlchemy(app)
        yield db
        db.session.remove()


def create_model(db):
    class Model1(db.Model):  # type: ignore[name-defined, misc]
        def __init__(
            self,
            test1=None,
            test2=None,
        ):
            self.test1 = test1
            self.test2 = test2

        id = Column(Integer, primary_key=True)
        test1 = Column(String(20))
        test2 = Column(String(20))

        def __unicode__(self):
            return self.test1

        def __str__(self):
            return self.test1

    db.create_all()

    return Model1


def test_xss(app, db, admin):
    Model1 = create_model(db)

    class MyModelView(ModelView):
        column_labels = {
            "test1": '<script>alert("XSS!")</script> <i class="fa fa-user"></i>Test 1',
            "test2": "<b>Test 2</b>",
        }

        column_filters = ["test1", "test2"]

    admin.add_view(MyModelView(Model1, db.session, category="XSS Tests"))

    client = app.test_client()
    rv = client.get("/admin/model1/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200

    assert '<i class="fa fa-user"></i>' in data
    assert "<b>Test 2</b>" in data
    assert '<script>alert("XSS!")</script>' not in data
