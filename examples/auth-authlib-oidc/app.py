import os

from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_login import login_user
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user, logout_user
from sqlalchemy.orm.exc import NoResultFound

import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_blueprint=False) # don't register the built-in login/logout/etc. views

# setup authlib
oauth = OAuth(app)
oauth.register(
    "oidc_sample",
    server_metadata_url=app.config["OIDC_SAMPLE_SERVER_METADATA_URL"],
    client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256"},
)


@app.route("/login")
def login():
    redirect_uri = url_for("oauth_callback", _external=True)
    return oauth.oidc_sample.authorize_redirect(redirect_uri)


app.login_manager.login_view = (
    "login"  # replace default form-based login page by OIDC based auth
)


@app.route("/oauth_callback")
def oauth_callback():
    token = oauth.oidc_sample.authorize_access_token()
    user_claims = oauth.oidc_sample.parse_id_token(token)
    email = user_claims.get("email")
    try:
        user = User.query.filter_by(email=email).one()
    except NoResultFound: # to support just-in-time provisionning
        user = User(first_name=user_claims.get("first_name"), last_name=user_claims.get("last_name"), email=email, active=True)
        db.session.add(user)
        db.session.commit()
    login_user(user)
    print(current_user.is_authenticated)
    return redirect("/admin/")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/admin/")


# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('login', next=request.url))

# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Create admin
admin = flask_admin.Admin(
    app,
    'Example: Auth with OIDC',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelView(User, db.session))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

    return


if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True)
