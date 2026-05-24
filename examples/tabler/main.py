import datetime
import os.path as op
import typing as t
from typing import Any

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
from flask_admin.theme import TablerTheme
from flask_admin.theme import TablerUITheme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from examples.tabler.data import build_sample_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = False

db = SQLAlchemy(app)


class MyAdminIndexView(AdminIndexView):
    """
    Let user dynamically change GLOBAL theme settings.
    Demo only.
    """

    extra_js = ["/static/js/active-layout.js"]

    def _theme(self):
        return getattr(self.admin, "theme", None)

    def _allowed_values(self, theme, field_name):
        ann = type(theme).__annotations__.get(field_name)
        if not ann or t.get_origin(ann) is not t.Literal:
            return None
        return t.get_args(ann)

    @expose("/set-theme")
    def set_theme_view(self):
        theme = self._theme()

        field = request.args.get("field")
        value = request.args.get("value")

        if theme and field and value:
            allowed = self._allowed_values(theme, field)

            if allowed and value in allowed:
                setattr(theme, field, value)

        next_url = request.args.get("next") or request.referrer
        return redirect(next_url or url_for("admin.index"))


admin = Admin(
    app,
    name="Example: Tabler",
    theme=TablerTheme(layout="fluid", theme_primary="purple"),
    index_view=MyAdminIndexView(),
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, default=datetime.datetime.now
    )

    def __repr__(self):
        return self.name


class Page(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64))
    content: Mapped[Text] = mapped_column(Text)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'")
    )

    def __repr__(self):
        return self.title


class ModelViewExtraJs(ModelView):
    extra_js = ["/static/js/active-layout.js"]


class UserAdmin(ModelViewExtraJs):
    column_searchable_list = ("name",)
    column_filters = ("name", "email")
    can_export = True
    export_types = ["csv", "xlsx"]
    can_set_page_size = True
    page_size_options = (3, 5, 7, 10, 20, 50, 100)
    page_size = 7


class SimplePageView(ModelViewExtraJs):
    can_view_details = True


class FileAdminExtraJs(FileAdmin):
    extra_js = ["/static/js/active-layout.js"]


class FileAdminModal(FileAdminExtraJs):
    rename_modal = True
    edit_modal = True
    mkdir_modal = True
    upload_modal = True


class PageWithModalView(ModelViewExtraJs):
    create_modal = True
    edit_modal = True
    details_modal = True
    can_view_details = True


with app.app_context():
    build_sample_db(db, User, Page)

if __name__ == "__main__":
    admin.add_view(
        UserAdmin(
            User,
            db,
            category="Menu",
            menu_icon_type="ti",
            menu_icon_value="user",
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
        ModelViewExtraJs(
            Page,
            db,
            name="Page-with-icon",
            endpoint="page2",
            menu_class_name="text-danger",
            menu_icon_type="ti",
            menu_icon_value="file",
        )
    )

    admin.add_view(FileAdminExtraJs("./", name="Local Files", category="Menu"))
    admin.add_view(
        FileAdminModal("./", name="Local Files with Modals", category="Menu")
    )

    admin.add_link(
        MenuLink(
            name="link1",
            url="http://www.example.com/",
            class_name="bg-primary link-light",
            icon_type="ti",
            icon_value="link",
        )
    )

    fields = (
        "layout",
        "theme_primary",
        "theme_base",
        "theme_font",
        "theme_radius",
    )

    options = {name: t.get_args(TablerUITheme.__annotations__[name]) for name in fields}

    for name, settings in options.items():
        for value in settings:
            admin.add_link(
                MenuLink(
                    name=str(value).replace("-", " ").title(),
                    url=f"/admin/set-theme?field={name}&value={value}",
                    category=name.replace("_", " ").title(),
                    icon_type="ti",
                    # have a different icon for layout and palette settings
                    icon_value="layout" if name == "layout" else "palette",
                    # CSS class for custom JS highlighting
                    class_name=f"user-{name}-options",
                ),
            )

    app_dir = op.realpath(op.dirname(__file__))
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not op.exists(database_path):
        with app.app_context():
            build_sample_db(db, User, Page)
    app.run(debug=True)
