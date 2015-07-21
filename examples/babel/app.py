from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin
from flask_babelex import Babel

from flask_admin.contrib import sqla

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '12345678'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Initialize babel
babel = Babel(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    return session.get('lang', 'en')


# Create models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    # Required for administrative interface
    def __unicode__(self):
        return self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    user = db.relationship(User, backref='posts')

    def __unicode__(self):
        return self.title


# Flask views
@app.route('/')
def index():
    tmp = u"""
<p><a href="/admin/?lang=en">Click me to get to Admin! (English)</a></p>
<p><a href="/admin/?lang=cs">Click me to get to Admin! (Czech)</a></p>
<p><a href="/admin/?lang=de">Click me to get to Admin! (German)</a></p>
<p><a href="/admin/?lang=es">Click me to get to Admin! (Spanish)</a></p>
<p><a href="/admin/?lang=fa">Click me to get to Admin! (Farsi)</a></p>
<p><a href="/admin/?lang=fr">Click me to get to Admin! (French)</a></p>
<p><a href="/admin/?lang=pt">Click me to get to Admin! (Portuguese)</a></p>
<p><a href="/admin/?lang=ru">Click me to get to Admin! (Russian)</a></p>
<p><a href="/admin/?lang=pa">Click me to get to Admin! (Punjabi)</a></p>
<p><a href="/admin/?lang=zh_CN">Click me to get to Admin! (Chinese - Simplified)</a></p>
<p><a href="/admin/?lang=zh_TW">Click me to get to Admin! (Chinese - Traditional)</a></p>
"""
    return tmp

if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 'Example: Babel')

    #admin.locale_selector(get_locale)

    # Add views
    admin.add_view(sqla.ModelView(User, db.session))
    admin.add_view(sqla.ModelView(Post, db.session))

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
