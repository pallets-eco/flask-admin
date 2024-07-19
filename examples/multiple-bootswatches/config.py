import os

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../flask-admin')))


class MyConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(16))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sqlite3-multiple-bootswatched.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class FlaskAdminConfig:
    BASIC_ADMIN_BOOTSWATCH_THEME = 'Cosmo'
    SUPER_ADMIN_BOOTSWATCH_THEME = 'United'

