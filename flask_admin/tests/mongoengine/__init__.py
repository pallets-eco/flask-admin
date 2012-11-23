from flask import Flask
from flask.ext.admin import Admin
from flask.ext.mongoengine import MongoEngine


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False
    app.config['MONGODB_SETTINGS'] = {'DB': 'tests'}

    db = MongoEngine()
    db.init_app(app)

    admin = Admin(app)

    return app, db, admin
