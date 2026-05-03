import pytest
from flask_admin import Admin
from flask_admin.contrib.sqla.view import ModelView
from flask_admin.theme import TablerTheme
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


@pytest.mark.parametrize(
    ("layout", "markers"),
    [
        ("vertical", ["data-tabler-layout=\"vertical\"", "tabler-admin-sidebar"]),
        (
            "fluid",
            [
                "data-tabler-layout=\"fluid\"",
                "class=\"layout-fluid\"",
                "tabler-admin-navbar-secondary",
            ],
        ),
        ("condensed", ["data-tabler-layout=\"condensed\"", "tabler-admin-navbar-collapse"]),
    ],
)
def test_layout_renders(app, babel, sqla_db_ext, layout, markers):
    admin = Admin(app, theme=TablerTheme(layout=layout))

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

        for marker in markers:
            assert marker in data

        assert "table table-vcenter table-striped table-hover" in data
        assert "column-header col-title" in data
        assert "column-header col-author-first_name" in data
