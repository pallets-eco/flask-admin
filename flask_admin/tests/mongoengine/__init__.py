import sys

from flask import Flask
from nose.plugins.skip import SkipTest

from flask_admin import Admin
from flask_admin._compat import PY2

# Skip test on PY3
if not PY2:
    raise SkipTest('The MongoEngine integration is not Python 3 compatible')

# Skip test on Python 2.6 since it is still supported by flask-admin:
if sys.version_info[0] == 2 and sys.version_info[1] == 6:
    raise SkipTest('MongoEngine is not Python 2.6 compatible as of its 0.11 version.')

from flask_mongoengine import MongoEngine


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False
    app.config['MONGODB_SETTINGS'] = {'DB': 'tests'}

    db = MongoEngine()
    db.init_app(app)

    admin = Admin(app)

    return app, db, admin
