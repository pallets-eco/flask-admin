import os

from flask_admin import Admin
from flask_admin.contrib import rediscli
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import FomanticUI
from models import db
from models import Post
from models import User
from redis import Redis
from wtforms.fields import StringField

from .views import IndexView


class UserModelView(ModelView):
    column_list = ["id", "email", "name", "age", "active", "created_at"]
    column_editable_list = ["active"]
    column_type_formatters = {bool: lambda v, value: "✔" if value else "–"}
    can_view_details = True
    can_set_page_size = True
    can_export = True
    export_types = ["pdf", "html", "json", "csv", "xlsx"][:1]
    column_filters = ("id", "email", "name", "age", "active", "created_at", "posts")
    page_size_options = (1, 5, 10, 20, 2000)
    column_searchable_list = ("email", "name", "id")
    column_descriptions = dict(
        email="User email address - this must be a valid email format and "
        "will be used for account verification and password reset requests",
        name="Full name of the user as it should appear on their profile "
        "and in communications. This field should contain the "
        "user's complete legal name or preferred display name, which "
        "will be used throughout the application interface, email notifications,"
        "and public-facing components. The name should be entered in a consistent "
        "format to maintain data quality and enable proper sorting and filtering "
        "capabilities. Special characters and numbers are allowed but should be used "
        "appropriately to reflect the user's actual name rather than nicknames "
        "or aliases",
        age="User age in years (must be 13 or older to comply with data"
        "protection regulations)",
        active="Whether the user account is active - inactive accounts "
        "cannot log in or perform any actions until reactivated by an administrator",
        created_at="Timestamp indicating when this user account "
        "was first created in the system",
        posts="Collection of all blog posts authored by this user - can be "
        "filtered and sorted by date, title or status",
    )
    form_extra_fields = {
        "Extra field": StringField(
            "Extra Field Name", render_kw={"dddd": 1, "append": "sdsd"}
        )
    }


class UserModelViewModal(UserModelView):
    create_modal = True
    edit_modal = True
    details_modal = True
    delete_modal = True


class PostModelView(ModelView):
    column_list = ["id", "title", "body", "author", "created_at"]
    column_editable_list = ["title"]
    can_view_details = True
    can_set_page_size = True
    can_export = True
    column_sortable_list = ["id"]
    export_types = ["pdf", "html", "json", "csv", "xlsx"]
    column_filters = ("id", "title", "body", "author", "created_at")
    column_searchable_list = ("title", "body")
    column_formatters = {
        "body": lambda v, c, m, p: m.body[:50] + "..." if m.body else ""
    }
    column_descriptions = dict(
        title="Post Title Description",
        body="Post Body Description",
        author="Author Description",
        created_at="Created At Description",
    )


class PostModelViewModal(PostModelView):
    create_modal = True
    edit_modal = True
    details_modal = True
    delete_modal = True


class MyFileAdmin(FileAdmin):
    rename_modal = True
    mkdir_modal = True
    upload_modal = True
    edit_modal = True
    can_rename = True
    can_delete_dirs = True
    can_mkdir = True
    can_download = True
    can_delete = True
    can_upload = True


class PlainFileAdmin(FileAdmin):
    can_rename = True
    can_delete_dirs = True
    can_mkdir = True
    can_download = True
    can_delete = True
    can_upload = True


admin = Admin(
    name="SuperAdmin",
    theme=FomanticUI(base_template="master.html"),
    index_view=IndexView("Home", endpoint="superadmin", url="/superadmin"),
)

v = rediscli.RedisCli(Redis(), "Redis Console", endpoint="s/rediscli")
v.menu_icon_value = "terminal"
admin.add_view(v)

_path_filemanager = os.path.join(os.path.dirname(__file__), "../")

admin.add_view(
    PlainFileAdmin(
        _path_filemanager,
        name="File Manager (Standart)",
        endpoint="s/filemanager",
        menu_icon_value="folder open",
        category="File Management",
    )
)
admin.add_view(
    MyFileAdmin(
        _path_filemanager,
        name="File Manager (Modal)",
        endpoint="s/filemanager_modal",
        menu_icon_value="file alternate",
        category="File Management",
    )
)

# Add a category for user views
admin.add_category("User Management", icon_value="users")

# Add both user model views (normal and modal) to the "User Management" category
admin.add_view(
    UserModelView(
        User,
        db.session,
        name="Users (Standard)",
        endpoint="s/user",
        menu_icon_type="default",
        menu_icon_value="user",
        category="User Management",
    )
)
admin.add_view(
    UserModelViewModal(
        User,
        db.session,
        name="Users (Modal)",
        endpoint="s/user_modal",
        menu_icon_type="default",
        menu_icon_value="user outline",
        category="User Management",
    )
)

# Add both post model views (normal and modal) to a "Post Management" category
admin.add_category("Post Management", icon_value="newspaper")
admin.add_view(
    PostModelView(
        Post,
        db.session,
        name="Posts (Standard)",
        endpoint="s/post",
        menu_icon_type="default",
        menu_icon_value="newspaper",
        category="Post Management",
    )
)
admin.add_view(
    PostModelViewModal(
        Post,
        db.session,
        name="Posts (Modal)",
        endpoint="s/post_modal",
        menu_icon_type="default",
        menu_icon_value="newspaper outline",
        category="Post Management",
    )
)

admin.add_category(
    "Other Models",
    icon_value="cubes",  # the icon name, e.g., FontAwesome 'cubes'
)

admin.add_view(
    PostModelView(
        Post,
        db.session,
        name="Other Posts",
        endpoint="s/otherposts",
        category="Other Models",
    )
)
admin.add_view(
    UserModelView(
        User,
        db.session,
        name="Other Users",
        endpoint="s/otherusers",
        category="Other Models",
    )
)


for i in range(1, 21):
    admin.add_view(
        PostModelView(Post, db.session, name=f"Posts {i}", endpoint=f"s/posts_{i}")
    )
