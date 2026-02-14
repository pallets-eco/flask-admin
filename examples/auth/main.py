import os
import random
import string

from flask import abort
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_security import current_user
from flask_security import RoleMixin
from flask_security import Security
from flask_security import SQLAlchemyUserDatastore
from flask_security import UserMixin
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from examples.auth.data import first_names
from examples.auth.data import last_names

app = Flask(__name__)

app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = False
# Flask-Security config
app.config["SECURITY_URL_PREFIX"] = "/admin"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = "ATGUOHAELKiubahiughaerGOJAEGj"
# Flask-Security URLs, overridden because they don't put a / at the end
app.config["SECURITY_LOGIN_URL"] = "/login/"
app.config["SECURITY_LOGOUT_URL"] = "/logout/"
app.config["SECURITY_REGISTER_URL"] = "/register/"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/admin/"
app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/"
# Flask-Security features
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
admin = Admin(
    app,
    name="Example: Auth",
    theme=Bootstrap4Theme(base_template="my_master.html"),
)


roles_users = Table(
    "roles_users",
    db.Model.metadata,
    Column("user_id", Integer(), ForeignKey("user.id")),
    Column("role_id", Integer(), ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean())
    confirmed_at: Mapped[DateTime | None] = mapped_column(DateTime())
    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    fs_uniquifier: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    def __str__(self):
        return self.email


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(ModelView):
    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and current_user.has_role("superuser")
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not
        accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for("security.login", next=request.url))


@app.route("/")
def index():
    return render_template("index.html")


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.theme.base_template,
        admin_view=admin.index_view,
        theme=admin.theme,
        h=admin_helpers,
        get_url=url_for,
    )


def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name="user")
        super_user_role = Role(name="superuser")
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        user_datastore.create_user(
            first_name="Admin",
            email="admin@example.com",
            password=hash_password("admin"),
            roles=[user_role, super_user_role],
        )

        for name, surname in zip(first_names, last_names, strict=True):
            tmp_email = f"{name.lower()}.{surname.lower()}@example.com"
            tmp_pass = "".join(
                random.choice(string.ascii_lowercase + string.digits) for i in range(10)
            )
            user_datastore.create_user(
                first_name=name,
                last_name=surname,
                email=tmp_email,
                password=hash_password(tmp_pass),
                roles=[
                    user_role,
                ],
            )
        db.session.commit()
    return


if __name__ == "__main__":
    admin.add_view(MyModelView(Role, db))
    admin.add_view(MyModelView(User, db))

    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    app.run(debug=True)
