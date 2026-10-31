import enum
from collections.abc import Callable
from typing import Any

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

app = Flask(__name__, template_folder="templates")
app.debug = True

talisman = Talisman(
    app,
    content_security_policy={
        "default-src": "'self'",
        "object-src": "'none'",
        "script-src": "'self' 'strict-dynamic'",
        "style-src": "'self' 'unsafe-inline' fonts.googleapis.com",
        "font-src": "'self' fonts.gstatic.com data: ",
        "img-src": "'self' data: ",
    },
    content_security_policy_nonce_in=["script-src", "style-src"],
)
# Get the CSP nonce generator from jinja environment globals which is added by Talisman
csp_nonce_generator: Callable[[], Any] = app.jinja_env.globals["csp_nonce"]  # type: ignore[assignment]


app.config.update(SECRET_KEY="dev", SQLALCHEMY_DATABASE_URI="sqlite:///sample.db")
db = SQLAlchemy(app)


class User(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))


class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class Fruit(enum.Enum):
    Apple = 1
    Banana = 2
    Orange = 3


class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    parent_id = db.Column(db.ForeignKey(Parent.id))

    # to test Select2 with modal
    fruit = db.Column(db.Enum(Fruit), nullable=True)

    parent = db.relationship(Parent, backref="children")


class UserView(ModelView):
    column_display_pk = True

    can_view_details = True
    column_filters = ["name"]


class UserModalView(ModelView):
    column_display_pk = True

    edit_modal = True
    create_modal = True
    details_modal = True
    can_view_details = True


class ParentView(ModelView):
    inline_models = [Child]
    can_view_details = True


class ParentWithModal(ModelView):
    can_view_details = True

    create_modal = True
    edit_modal = True
    details_modal = True

    inline_models = [Child]


class MyFileAdmin(FileAdmin):
    editable_extensions = ["txt"]


class FileAdminModal(FileAdmin):
    editable_extensions = ["txt"]
    rename_modal = True
    edit_modal = True
    mkdir_modal = True
    upload_modal = True


admin = Admin(
    app,
    name="Example: Simple Views",
    theme=Bootstrap4Theme(),
    csp_nonce_generator=csp_nonce_generator,
)

# parent_view = ParentView(Parent, db.session, category="Menu")
admin.add_view(UserView(User, db, category="Menu"))
admin.add_view(
    UserModalView(
        User, db, category="Menu", endpoint="user-modal", name="User with Modal"
    )
)
admin.add_view(ParentView(Parent, db, category="Menu"))
admin.add_view(
    ParentWithModal(
        Parent,
        db,
        category="Menu",
        endpoint="parent-with-modal",
        name="Parent with Modal",
    )
)

admin.add_view(MyFileAdmin("files/", category="Menu", name="Files"))
admin.add_view(FileAdminModal("files/", category="Menu", name="Files with Modals"))


with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.add_all([User(key=k, name=f"StrKey {k}") for k in range(5)])
    child1 = Child(name="Child 1", parent=Parent(name="Parent 1"))
    child2 = Child(name="Child 2", parent=Parent(name="Parent 1"))
    child3 = Child(name="Child 3", parent=Parent(name="Parent 2"))
    db.session.add_all([child1, child2, child3])
    db.session.commit()


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == "__main__":
    app.run(debug=True)
