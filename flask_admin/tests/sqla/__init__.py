from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
    app.config['SQLALCHEMY_ECHO'] = True

    db = SQLAlchemy(app)
    admin = Admin(app)

    return app, db, admin
