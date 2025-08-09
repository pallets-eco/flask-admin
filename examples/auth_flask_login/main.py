import os
import typing as t
from uuid import uuid4

import flask_login
from flask import flash
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from wtforms import fields
from wtforms import PasswordField
from wtforms import validators

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = False
db = SQLAlchemy(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")


# inherit from flask_login.UserMixin so no need to define login methods
class User(db.Model, flask_login.UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(
        String(80),
        unique=True,
        index=True,
    )
    # having a _ will make the field hidden in flask-admin edit/create forms
    _password = Column(String(128), nullable=True)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        # Check if this is actually a new password to avoid unnecessary updates
        if not password:
            return
        if self._password is None or not self.check_password(password):
            self._password = generate_password_hash(
                password,
                # on MacOS, default method="scrypt" gives AttributeError
                method="pbkdf2",
            )
            self.alternative_id = uuid4().hex  # type: ignore[assignment]
            # password.setter can be called even without any user logged in, e.g.
            # when creating db
            if flask_login.current_user and flask_login.current_user == self:
                # changing the alternative id will log out even current session
                # so if current user changes pw, we must log her back
                flask_login.login_user(self)

    def check_password(self, password: t.Optional[str]) -> bool:
        if password is not None:
            return check_password_hash(self._password, password)
        return False

    # security: https://flask-login.readthedocs.io/en/latest/#alternative-tokens
    # allows logout users
    alternative_id = Column(String(32), default=uuid4().hex, index=True)

    def get_id(self):
        """
        Override flask_login.UserMixin.get_id to return alternative_id for security.
        """
        return self.alternative_id

    def __repr__(self):
        return self.username

    @staticmethod
    def get(data, field) -> t.Optional["User"]:
        return db.session.execute(
            db.select(User).where(getattr(User, field) == data)
        ).scalar()


@login_manager.user_loader
def load_user(alternative_id):
    return User.get(alternative_id, field="alternative_id")


class LoginForm(FlaskForm):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    user: t.Optional[User] = None  # To store the authenticated user for later use

    def validate_username(self, field):
        self.user = User.get(field.data, "username")
        if self.user is None:
            raise validators.ValidationError("Invalid username")

    def validate_password(self, field):
        if self.user is None:
            # Skip password check if username validation already failed
            return
        if not self.user.check_password(field.data):
            raise validators.ValidationError("Invalid password")


class RegistrationForm(FlaskForm):
    username = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_username(self, field):
        if User.get(field.data, "username"):
            raise validators.ValidationError("Username already taken")


# Create customized model view class
class MyModelView(ModelView):
    column_exclude_list = (
        "_password",
        "alternative_id",
    )
    column_editable_list = ("username",)  # allow inline editing
    form_excluded_columns = ("alternative_id",)
    # password is a property, so we cannot use flask_admin.ModelView.column_list to
    # include the password property in forms
    form_extra_fields = {
        "password": PasswordField("Password"),
    }

    def is_accessible(self):
        """Check if current user can access admin interface"""
        return flask_login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible"""
        flash("Please login to access this page.", "danger")
        return redirect(url_for("admin.login_view", next=request.url))


# Create customized index view class that handles login & registration
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not flask_login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for(".index"))

        # handle user login
        form = LoginForm(request.form)
        if form.validate_on_submit():
            user = form.user
            flask_login.login_user(user)
            # rredirect to next
            if "next" in request.args:
                next_url = request.args.get("next")
                if next_url:
                    return redirect(next_url)
            return redirect(url_for(".index"))

        link = (
            "<p>Don't have an account? <a href=\""
            + url_for(".register_view")
            + '">Click here to register.</a></p>'
        )
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super().index()

    @expose("/register/", methods=("GET", "POST"))
    def register_view(self):
        form = RegistrationForm(request.form)
        if form.validate_on_submit():
            user = User()
            form.populate_obj(user)
            db.session.add(user)
            db.session.commit()
            flask_login.login_user(user)
            return redirect(url_for(".index"))
        link = (
            '<p>Already have an account? <a href="'
            + url_for(".login_view")
            + '">Click here to log in.</a></p>'
        )
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super().index()

    @expose("/logout/")
    def logout_view(self):
        flask_login.logout_user()
        return redirect(url_for(".index"))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    import random
    import string

    db.drop_all()
    db.create_all()
    test_user = User(username="test", password="test")
    db.session.add(test_user)
    names = [
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
    users = []
    for name in names:
        password = "".join(
            random.choice(string.ascii_lowercase + string.digits) for i in range(10)
        )
        users.append(
            User(
                username=name,
                password=password,
            )
        )
    # execute insert uses a bulk insert which is more efficient
    db.session.add_all(users)
    db.session.commit()


if __name__ == "__main__":
    admin = Admin(
        app,
        name="Example: Auth",
        index_view=MyAdminIndexView(),
        theme=Bootstrap4Theme(base_template="my_master.html", fluid=True),
    )

    admin.add_view(MyModelView(User, db.session))

    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    app.run(debug=True)
