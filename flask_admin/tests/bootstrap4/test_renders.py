from flask_admin.contrib.sqla.view import ModelView
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship


def create_models(db):
    class User(db.Model):  # type: ignore[name-defined, misc]
        def __init__(
            self,
            first_name=None,
            last_name=None,
        ):
            self.first_name = first_name
            self.last_name = last_name

        id = Column(Integer, primary_key=True)
        first_name = Column(String(20))
        last_name = Column(String(20))

        def __unicode__(self):
            return self.first_name

        def __str__(self):
            return self.first_name

    class Post(db.Model):  # type: ignore[name-defined, misc]
        def __init__(self, title=None, desc=None, author=None):
            self.title = title
            self.desc = desc
            self.author = author

        id = Column(Integer, primary_key=True)
        title = Column(String(20))
        desc = Column(String(20))
        author_id = Column(Integer, ForeignKey("user.id"))
        author = relationship("User", backref=backref("posts", lazy="dynamic"))

    db.create_all()

    return User, Post


def fill_data(db, User, Post):
    u1 = User("user1", "userdesc1")
    u2 = User("user2", "userdesc2")

    db.session.add_all(
        [
            u1,
            u2,
            Post("post1", "postdesc1", u1),
            Post("post2", "postdesc2", u2),
        ]
    )
    db.session.commit()


def test_css_class_with_combined(app, db, admin):
    with app.app_context():
        User, Post = create_models(db)
        fill_data(db, User, Post)

        class PostView(ModelView):
            column_list = ["title", "author.first_name"]

        admin.add_view(PostView(Post, db.session))

        client = app.test_client()
        response = client.get("/admin/post/")
        data = response.data.decode("utf-8")
        assert response.status_code == 200

        # Check that bootstrap4 classes are present
        assert "table table-striped table-bordered table-hover" in data

        # Check that custom column classes are applied
        assert "column-header col-title" in data
        assert "column-header col-author-first_name" in data


# FIXME: move all bootstrap4 tests to here
