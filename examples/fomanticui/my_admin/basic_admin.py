from flask import flash
from flask_admin import actions
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import FomanticUI
from models import db
from models import Post
from models import User

from .views import IndexView


class CustomUserModelView(ModelView):
    column_editable_list = ["active"]
    can_view_details = True
    can_create = False
    can_delete = False
    can_edit = False
    page_size_options = (1, 5, 10, 20)
    simple_list_pager = True
    can_set_page_size = True
    page_size = 5
    column_default_sort = "age"
    column_list = ("age", "email", "name", "age", "active", "balance")

    @actions.action(
        "custom_action", "Custom Action", "Are you sure you want to do this?"
    )
    def custom_action(self, ids):
        flash("Done!")


class PostModelView(ModelView):
    can_create = False
    can_delete = False
    can_edit = False
    column_list = ["id", "title", "body", "author", "created_at"]
    column_editable_list = ["title"]


admin = Admin(
    name="BasicAdmin",
    theme=FomanticUI(base_template="master.html"),
    index_view=IndexView("Home", endpoint="basicadmin", url="/basicadmin"),
)


admin.add_view(CustomUserModelView(User, db.session, name="Users", endpoint="b/users"))
admin.add_view(PostModelView(Post, db.session, name="Posts", endpoint="b/posts"))
