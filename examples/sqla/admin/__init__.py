from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel
import os
import os.path as op

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

# Build a sample db on the fly, if one does not exist yet.
app_dir = os.path.realpath(os.path.dirname(__file__))
database_path = op.join(app_dir, app.config['DATABASE_FILE'])
if not os.path.exists(database_path):
    from admin.data import build_sample_db
    build_sample_db()

# Initialize babel
babel = Babel(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    return session.get('lang', 'en')


import admin.main
