import os


class MyConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(16))
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///sqlite3-fomanticui.sqlite")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
