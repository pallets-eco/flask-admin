from flask import Flask
from flask import request
from flask import session
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile("config.py")
db = SQLAlchemy(app)


def get_locale():
    override = request.args.get("lang")

    if override:
        session["lang"] = override

    return session.get("lang", "en")


# Initialize babel
babel = Babel(app, locale_selector=get_locale)


# Initialize babel
babel = Babel(app, locale_selector=get_locale)


import admin.main
