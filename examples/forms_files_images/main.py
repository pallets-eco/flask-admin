import os
import os.path as op

import jinja2.runtime
from flask import Flask
from flask import url_for
from flask_admin import Admin
from flask_admin import form
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from wtforms import fields
from wtforms import widgets

from examples.forms_files_images.data import first_names
from examples.forms_files_images.data import last_names
from examples.forms_files_images.data import locations

app = Flask(__name__, static_folder="files")
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = False
db = SQLAlchemy(app)
admin = Admin(app, name="Example: Forms", theme=Bootstrap4Theme(swatch="cerulean"))


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), "files")
try:
    os.mkdir(file_path)
except OSError:
    pass


class File(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    path = mapped_column(String(128))

    def __String__(self):
        return self.name


class Image(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String(128))

    def __String__(self):
        return self.name


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str] = mapped_column(String(32))
    city: Mapped[str] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class Page(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)

    def __String__(self):
        return self.name


# Delete hooks for models, delete files if models are getting deleted
@listens_for(File, "after_delete")
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            # Don't care if was not deleted because it does not exist
            pass


@listens_for(Image, "after_delete")
def del_image(mapper, connection, target):
    if target.path:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path, form.thumbgen_filename(target.path)))
        except OSError:
            pass


# define a custom wtforms widget and field.
# see https://wtforms.readthedocs.io/en/latest/widgets.html#custom-widgets
class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        # add WYSIWYG class to existing classes
        existing_classes = kwargs.pop("class", "") or kwargs.pop("class_", "")
        kwargs["class"] = "{} {}".format(existing_classes, "ckeditor")
        return super().__call__(field, **kwargs)


class CKTextAreaField(fields.TextAreaField):
    widget = CKTextAreaWidget()


class PageView(ModelView):
    form_overrides = {"text": CKTextAreaField}
    create_template = "create_page.html"
    edit_template = "edit_page.html"


class FileView(ModelView):
    # Override form field to use Flask-Admin FileUploadField
    form_overrides = {"path": form.FileUploadField}

    # Pass additional parameters to 'path' to FileUploadField constructor
    form_args = {
        "path": {"label": "File", "base_path": file_path, "allow_overwrite": False}
    }


class ImageView(ModelView):
    def _list_thumbnail(
        view, context: jinja2.runtime.Context | None, model, name: str
    ) -> str | Markup:
        if not model.path:
            return ""

        return Markup(
            '<img src="{}">'.format(
                url_for("static", filename=form.thumbgen_filename(model.path))
            )
        )

    column_formatters = {"path": _list_thumbnail}

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        "path": form.ImageUploadField(
            "Image", base_path=file_path, thumbnail_size=(100, 100, True)
        )
    }


class UserView(ModelView):
    """
    This class demonstrates the use of 'rules' for controlling the rendering of forms.
    """

    form_create_rules = [
        # Header and four fields. Email field will go above phone field.
        rules.FieldSet(
            ("first_name", "last_name", "email", "phone", "is_admin"), "Personal"
        ),
        # Separate header and few fields
        rules.Header("Location"),
        rules.Field("city"),
        # String is resolved to form field, so there's no need to explicitly use
        # `rules.Field`
        "country",
        # Show macro that's included in the templates
        rules.Container("rule_demo.wrap", rules.Field("notes")),
    ]

    # Use same rule set for edit page
    form_edit_rules = form_create_rules

    create_template = "create_user.html"
    edit_template = "edit_user.html"

    column_descriptions = {
        "is_admin": "Is this an admin user?",
    }


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import random
    import string

    db.drop_all()
    db.create_all()

    users = []
    for name, surname, location in zip(
        first_names, last_names, locations, strict=False
    ):
        tmp = "".join(random.choice(string.digits) for i in range(10))
        phone = f"({tmp[0:3]}) {tmp[3:6]} {tmp[6::]}"
        users.append(
            User(
                first_name=name,
                last_name=surname,
                email=f"{name.lower()}.{surname.lower()}@example.com",
                phone=phone,
                city=location[0],
                country=location[1],
            )
        )

    images = ["Buffalo", "Elephant", "Leopard", "Lion", "Rhino"]
    images_objects = [Image(name=name, path=f"{name.lower()}.jpg") for name in images]
    files = [File(name=f"Example {str(i)}") for i in range(1, 4)]

    db.session.add_all(users + images_objects + files)

    sample_text = (
        "<h2>This is a test</h2>"
        "<p>Create HTML content in a text area field with the help of "
        "<i>WTForms</i> and <i>CKEditor</i>.</p>"
    )
    db.session.add(Page(name="Test Page", text=sample_text))

    db.session.commit()


if __name__ == "__main__":
    admin.add_view(FileView(File, db))
    admin.add_view(ImageView(Image, db))
    admin.add_view(UserView(User, db))
    admin.add_view(PageView(Page, db))

    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    app.run(debug=True)
