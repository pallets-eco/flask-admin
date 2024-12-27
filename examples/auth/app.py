import os

import flask_admin
from flask import abort
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_admin import helpers as admin_helpers
from flask_admin.contrib import sqla
from flask_admin.theme import Bootstrap4Theme
from flask_security import current_user
from flask_security import RoleMixin
from flask_security import Security
from flask_security import SQLAlchemyUserDatastore
from flask_security import UserMixin
from flask_security.utils import hash_password
from flask_sqlalchemy import SQLAlchemy

# Create Flask application
app = Flask(__name__)
app.config.from_pyfile("config.py")
db = SQLAlchemy(app)


# Define models
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)

    def __str__(self):
        return self.email


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(sqla.ModelView):
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
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for("security.login", next=request.url))


# Flask views
@app.route("/")
def index():
    return render_template("index.html")


# Create admin
admin = flask_admin.Admin(
    app,
    "Example: Auth",
    theme=Bootstrap4Theme(base_template="my_master.html"),
)

# Add model views
admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelView(User, db.session))


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

    import random
    import string

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

        first_names = [
            "Harry",
            "Amelia",
            "Oliver",
            "Jack",
            "Isabella",
            "Charlie",
            "Sophie",
            "Mia",
            "Jacob",
            "Thomas",
            "Emily",
            "Lily",
            "Ava",
            "Isla",
            "Alfie",
            "Olivia",
            "Jessica",
            "Riley",
            "William",
            "James",
            "Geoffrey",
            "Lisa",
            "Benjamin",
            "Stacey",
            "Lucy",
        ]
        last_names = [
            "Brown",
            "Smith",
            "Patel",
            "Jones",
            "Williams",
            "Johnson",
            "Taylor",
            "Thomas",
            "Roberts",
            "Khan",
            "Lewis",
            "Jackson",
            "Clarke",
            "James",
            "Phillips",
            "Wilson",
            "Ali",
            "Mason",
            "Mitchell",
            "Rose",
            "Davis",
            "Davies",
            "Rodriguez",
            "Cox",
            "Alexander",
        ]

        for i in range(len(first_names)):
            tmp_email = (
                first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            )
            tmp_pass = "".join(
                random.choice(string.ascii_lowercase + string.digits) for i in range(10)
            )
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=hash_password(tmp_pass),
                roles=[
                    user_role,
                ],
            )
        db.session.commit()
    return


if __name__ == "__main__":
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    # Start app
    app.run(debug=True)
