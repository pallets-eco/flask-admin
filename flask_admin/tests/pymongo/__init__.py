import pymongo

from flask import Flask
from flask_admin import Admin


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'

    conn = pymongo.Connection()
    db = conn.tests

    admin = Admin(app)

    return app, db, admin
