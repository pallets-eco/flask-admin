from flask import Flask
from flask import request
from flask import session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
admin = Admin(app, name="Example: Babel")


def get_locale():
    override = request.args.get("lang")

    if override:
        session["lang"] = override

    return session.get("lang", "en")


babel = Babel(app, locale_selector=get_locale)


class User(db.Model):  # type: ignore[name-defined]
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    # Required for administrative interface
    def __unicode__(self):
        return self.username


class Post(db.Model):  # type: ignore[name-defined]
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    user = db.relationship(User, backref="posts")

    def __unicode__(self):
        return self.title


@app.route("/")
def index():
    tmp = """
<p><a href="/admin/?lang=en">Click me to get to Admin! (English)</a></p>
<p><a href="/admin/?lang=cs">Click me to get to Admin! (Czech)</a></p>
<p><a href="/admin/?lang=de">Click me to get to Admin! (German)</a></p>
<p><a href="/admin/?lang=es">Click me to get to Admin! (Spanish)</a></p>
<p><a href="/admin/?lang=fa">Click me to get to Admin! (Farsi)</a></p>
<p><a href="/admin/?lang=fr">Click me to get to Admin! (French)</a></p>
<p><a href="/admin/?lang=pt">Click me to get to Admin! (Portuguese)</a></p>
<p><a href="/admin/?lang=ru">Click me to get to Admin! (Russian)</a></p>
<p><a href="/admin/?lang=tr">Click me to get to Admin! (Turkish)</a></p>
<p><a href="/admin/?lang=pa">Click me to get to Admin! (Punjabi)</a></p>
<p><a href="/admin/?lang=zh_CN">Click me to get to Admin! (Chinese - Simplified)</a></p>
<p>
<a href="/admin/?lang=zh_TW">Click me to get to Admin! (Chinese - Traditional)</a>
</p>
"""
    return tmp


if __name__ == "__main__":
    # admin.locale_selector(get_locale)
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Post, db.session))

    with app.app_context():
        db.create_all()

    app.run(debug=True)
