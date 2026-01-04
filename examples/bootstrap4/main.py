import datetime
import os.path as op

from flask import Flask
from flask import redirect
from flask import request
from flask import url_for
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin import expose
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuDivider
from flask_admin.menu import MenuLink
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)


class MyAdminIndexView(AdminIndexView):
    def set_theme(self):
        reqTheme = request.args.get("theme")
        cookTheme = request.cookies.get("theme")

        t = reqTheme or cookTheme or "cosmo"

        if self.admin and self.admin.theme:
            if hasattr(self.admin.theme, "swatch"):
                self.admin.theme.swatch = t

    @expose("/change-theme")
    def change_theme(self):
        self.set_theme()

        next = request.args.get("next")

        return redirect(next or url_for("admin.index"))


admin = Admin(
    app,
    name="Example: Bootstrap4",
    theme=Bootstrap4Theme(swatch="cosmo"),
    index_view=MyAdminIndexView(),
    category_icon_classes={
        "Menu": "fa fa-cog text-danger",
    },
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __unicode__(self):
        return self.name


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(64))
    content = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


class UserAdmin(ModelView):
    column_searchable_list = ("name",)
    column_filters = ("name", "email")
    can_export = True
    export_types = ["csv", "xlsx"]
    can_set_page_size = True
    page_size_options = (3, 5, 7, 10, 20, 50, 100)
    page_size = 7


class SimplePageView(ModelView):
    can_view_details = True


class FileAdminModal(FileAdmin):
    rename_modal = True
    edit_modal = True
    mkdir_modal = True
    upload_modal = True


class PageWithModalView(ModelView):
    create_modal = True
    edit_modal = True
    details_modal = True
    can_view_details = True


with app.app_context():
    from data import build_sample_db

    build_sample_db(db, User, Page)

if __name__ == "__main__":
    # Icons reference (FontAwesome v4):
    # https://fontawesome.com/v4/icons/

    from data import all_themes

    admin.add_view(
        UserAdmin(
            User,
            db,
            category="Menu",
            menu_icon_type="fa",
            menu_icon_value="fa-users",
            menu_class_name="text-warning",
        )
    )
    admin.add_menu_item(MenuDivider(), target_category="Menu")
    admin.add_view(SimplePageView(Page, db, category="Menu", name="Simple Page"))

    admin.add_view(
        PageWithModalView(
            Page, db, category="Menu", endpoint="page-modal", name="Page-Modal"
        )
    )

    admin.add_view(
        ModelView(
            Page,
            db,
            name="Page-with-icon",
            endpoint="page2",
            menu_class_name="text-danger",
            menu_icon_type="fa",
            menu_icon_value="fa-file",
        )
    )

    admin.add_view(FileAdmin("files/", name="Local Files", category="Menu"))
    admin.add_view(
        FileAdminModal("files/", name="Local Files with Modals", category="Menu")
    )

    admin.add_link(
        MenuLink(
            name="link1",
            url="http://www.example.com/",
            class_name="text-warning bg-danger",
            icon_type="fa",
            icon_value="fa-external-link",
        )
    )
    admin.add_link(
        MenuLink(name="link2", url="http://www.example.com/", class_name="text-danger")
    )
    admin.add_link(MenuLink(name="Link3", url="http://www.example.com/"))

    admin.add_sub_category(name="Links", parent_name="Menu")
    admin.add_link(
        MenuLink(
            name="External link",
            url="http://www.example.com/",
            category="Links",
            class_name="text-info",
            icon_type="fa",
            icon_value="fa-external-link",
        )
    )
    admin.add_link(
        MenuLink(
            name="External link",
            url="http://www.example.com/",
            category="Links",
            class_name="text-success",
        )
    )
    admin.add_menu_item(MenuDivider(), target_category="Links")
    admin.add_link(
        MenuLink(name="External link", url="http://www.example.com/", category="Links")
    )

    for t in all_themes:
        admin.add_link(
            MenuLink(
                name=f"{t.title()}",
                url=f"/admin/change-theme?theme={t}&next=/admin/user/",
                category="Themes",
            )
        )

    app_dir = op.realpath(op.dirname(__file__))
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not op.exists(database_path):
        with app.app_context():
            build_sample_db(db, User, Page)

    app.run(debug=True)
