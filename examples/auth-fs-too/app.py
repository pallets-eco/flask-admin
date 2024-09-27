"""
A complete but simple application utilizing Flask-Security-Too for authorization
and authentication.

Supports i18n by adding ?lang=xx.
Since this is session based - lang is only evaluated on FIRST request - even after
logout. So to change languages you probably need to delete the session cookie.
"""


import os
from flask import Flask, flash, url_for, redirect, render_template, request, session, abort
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    current_user, hash_password, reset_password_instructions_sent

from flask_security.models import fsqla
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
fsqla.FsModels.set_db_info(db)


# Define models
class Role(db.Model, fsqla.FsRoleMixin):
    def __str__(self):
        return self.name
    pass


class User(db.Model, fsqla.FsUserMixin):
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))

    def __str__(self):
        return self.email
    pass


# Setup Babel
babel = Babel(app)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@babel.localeselector
def get_locale():
    # Mostly for testing for a given session - set lang based on first request.
    # Honor explicit url request first
    if "lang" not in session:
        locale = request.args.get("lang", None)
        if not locale:
            locale = request.accept_languages.best
        if locale:
            session["lang"] = locale
    return session.get("lang", "en").replace("-", "_")


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
                return redirect(url_for('security.login', next=request.url))

# Flask views
@app.route('/')
def index():
    return render_template('index.html')


# Create admin
admin = flask_admin.Admin(
    app,
    'Example: Auth Flask-Security-Too',
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


@reset_password_instructions_sent.connect_via(app)
def on_reset(myapp, user, token):
    # Since we don't have email - just flash the token!
    # Normal path is the email has this URL in it, and user clicks on it.
    flash("Go to /admin/reset/{}".format(token))


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

        test_user = user_datastore.create_user(
            first_name='Admin',
            email='admin@example.com',
            password=hash_password('admin'),
            roles=[user_role, super_user_role]
        )

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]
        last_names = [
            'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
            'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
            'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
        ]

        for i in range(len(first_names)):
            tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
            tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
            user_datastore.create_user(
                first_name=first_names[i],
                last_name=last_names[i],
                email=tmp_email,
                password=hash_password(tmp_pass),
                roles=[user_role, ]
            )
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
