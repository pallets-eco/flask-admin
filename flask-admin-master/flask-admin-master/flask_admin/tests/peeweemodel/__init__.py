from flask import Flask
from flask_admin import Admin
import peewee


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

    db = peewee.SqliteDatabase(':memory:')
    admin = Admin(app)

    return app, db, admin
