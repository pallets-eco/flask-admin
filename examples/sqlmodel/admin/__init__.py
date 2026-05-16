from pathlib import Path

from flask import Flask
from flask import request
from flask import session
from flask_babel import Babel
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_FILE = INSTANCE_DIR / "db.sqlite"

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = str(DATABASE_FILE)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE.as_posix()}"
app.config["SQLALCHEMY_ECHO"] = False

engine = create_engine(
    app.config["SQLALCHEMY_DATABASE_URI"],
    echo=app.config["SQLALCHEMY_ECHO"],
)
db_session = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)


def get_locale():
    override = request.args.get("lang")

    if override:
        session["lang"] = override

    return session.get("lang", "en")


babel = Babel(app, locale_selector=get_locale)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


import admin.main  # noqa: F401, E402
