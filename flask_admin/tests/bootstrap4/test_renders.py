from flask_admin.contrib.sqla.view import ModelView
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship


def create_models(sqla_db_ext):
    class User(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "user"
        id = Column(Integer, primary_key=True)
        first_name = Column(String(20))
        last_name = Column(String(20))

        def __str__(self):
            return self.first_name

    class Post(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
        __tablename__ = "post"
        id = Column(Integer, primary_key=True)
        title = Column(String(20))
        desc = Column(String(20))
        author_id = Column(Integer, ForeignKey("user.id"))
        author = relationship("User", backref=backref("posts", lazy="dynamic"))

    sqla_db_ext.create_all()

    return User, Post


def fill_data(sqla_db_ext, User, Post):
    u1 = User(first_name="user1", last_name="userdesc1")
    u2 = User(first_name="user2", last_name="userdesc2")

    sqla_db_ext.db.session.add_all(
        [
            u1,
            u2,
            Post(title="post1", desc="postdesc1", author=u1),
            Post(title="post2", desc="postdesc2", author=u2),
        ]
    )
    sqla_db_ext.db.session.commit()


def test_css_class_with_combined(app, sqla_db_ext, admin):
    with app.app_context():
        User, Post = create_models(sqla_db_ext)
        fill_data(sqla_db_ext, User, Post)

        class PostView(ModelView):
            column_list = ["title", "author.first_name"]

        admin.add_view(PostView(Post, sqla_db_ext.db))

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
