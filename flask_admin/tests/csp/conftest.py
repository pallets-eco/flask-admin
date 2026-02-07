import pytest
from flask_admin.base import Admin
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
    # app.config["SQLALCHEMY_ECHO"] = True
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    yield db

    with app.app_context():
        db.session.close()
        db.engine.dispose()


@pytest.fixture
def admin(app, babel, nonce):
    def csp_nonce_generator():
        return nonce

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin
