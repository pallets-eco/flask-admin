from flask import Flask
from flask_admin import Admin


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False

    admin = Admin(app)
    return app, admin
