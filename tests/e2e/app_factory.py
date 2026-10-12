"""Flask app factory for Tabler-theme end-to-end tests.

Builds a small SQLAlchemy-backed admin (Author with inline Books, plus a
FileAdmin instance) rendered with the Tabler theme.
"""

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import TablerTheme
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import InputRequired

db = SQLAlchemy()


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    def __str__(self):
        return self.name


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey(Author.id))
    author = db.relationship(Author, backref="books")

    def __str__(self):
        return self.title


class AuthorView(ModelView):
    can_view_details = True
    column_searchable_list = ["name"]
    form_args = {
        "name": {"validators": [InputRequired()]},
    }
    inline_models = (Book,)


def create_app(workdir):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "tabler-e2e-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{workdir / 'e2e.db'}"
    # The live server runs in a separate thread, so allow cross-thread use.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False}
    }

    Babel(app)
    db.init_app(app)

    admin = Admin(app, name="Tabler e2e", theme=TablerTheme())
    admin.add_view(AuthorView(Author, db.session))

    files_dir = workdir / "files"
    files_dir.mkdir(exist_ok=True)
    admin.add_view(FileAdmin(str(files_dir), "/files/", name="Files"))

    return app
