from flask import Flask
from flask import request
from flask import session
from flask_babel import Babel
from sqlmodel import create_engine
from sqlmodel import SQLModel

app = Flask(__name__)
app.config.from_pyfile("config.py")
# 1. Create engine (same as `SQLAlchemy(app)` would do internally)
engine = create_engine(
    app.config["SQLALCHEMY_DATABASE_URI"], echo=app.config.get("SQLALCHEMY_ECHO", True)
)


# 2. Create the database tables
def init_db():
    SQLModel.metadata.create_all(engine)


def get_locale():
    override = request.args.get("lang")

    if override:
        session["lang"] = override

    return session.get("lang", "en")


# Initialize babel
babel = Babel(app, locale_selector=get_locale)


import admin.main  # noqa: F401, E402
