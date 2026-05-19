from flask import redirect
from flask import url_for
from flask_admin import Admin
from flask_admin.base import MenuLink
from flask_admin.contrib.sqlmodel import ModelView
from flask_admin.theme import Bootstrap4Theme
from wtforms import validators

from . import app
from . import db_session
from .models import Post
from .models import Tag
from .models import Tree
from .models import User


@app.route("/")
def index():
    return """
<p><a href="/admin/?lang=en">Click me to get to Admin! (English)</a></p>
<p><a href="/admin/?lang=cs">Click me to get to Admin! (Czech)</a></p>
<p><a href="/admin/?lang=de">Click me to get to Admin! (German)</a></p>
<p><a href="/admin/?lang=es">Click me to get to Admin! (Spanish)</a></p>
<p><a href="/admin/?lang=fr">Click me to get to Admin! (French)</a></p>
<p><a href="/admin/?lang=zh_CN">Click me to get to Admin! (Chinese - Simplified)</a></p>
"""


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="/favicon.ico"))


class UserAdmin(ModelView):
    can_set_page_size = True
    page_size = 10
    page_size_options = (10, 20, 50)
    can_view_details = True
    column_list = ["id", "type", "first_name", "last_name", "email", "timezone"]
    column_searchable_list = ["first_name", "last_name", "email"]
    column_editable_list = []
    form_columns = [
        "type",
        "first_name",
        "last_name",
        "email",
        "website",
        "ip_address",
        "currency",
        "timezone",
        "dialling_code",
        "local_phone_number",
        "featured_post",
    ]

    form_args = {
        "local_phone_number": {
            "label": "Phone number",
            "validators": [validators.Length(min=10, max=10)],
        }
    }


class PostAdmin(ModelView):
    column_display_pk = True
    column_list = ["id", "title", "user", "date", "created_at"]
    column_searchable_list = ["title"]
    form_columns = ["title", "text", "date", "background_color", "user", "tags"]
    form_widget_args = {"text": {"rows": 8}}
    can_export = True
    export_types = ["csv", "xls"]


class TreeAdmin(ModelView):
    list_template = "tree_list.html"
    column_list = ["id", "name", "parent"]
    form_columns = ["name", "parent"]

    def render(self, template, **kwargs):
        return super().render(template, foo="bar", **kwargs)


admin = Admin(app, name="Example: SQLModel", theme=Bootstrap4Theme(swatch="default"))
admin.add_view(UserAdmin(User, db_session))
admin.add_view(ModelView(Tag, db_session))
admin.add_view(PostAdmin(Post, db_session))
admin.add_view(TreeAdmin(Tree, db_session, category="Other"))
admin.add_sub_category(name="Links", parent_name="Other")
admin.add_link(MenuLink(name="Back Home", url="/", category="Links"))
admin.add_link(
    MenuLink(name="External link", url="http://www.example.com/", category="Links")
)
