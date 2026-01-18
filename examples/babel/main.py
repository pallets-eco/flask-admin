from flask import Flask
from flask import request
from flask import session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_ECHO"] = False
db = SQLAlchemy(app)
admin = Admin(app, name="Example: Babel")


def get_locale():
    override = request.args.get("lang")

    if override:
        session["lang"] = override

    return session.get("lang", "en")


babel = Babel(app, locale_selector=get_locale)


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)

    # flask-admin shows __repr__ output in its interface
    def __repr__(self):
        return self.username


class Post(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    date: Mapped[DateTime] = mapped_column(DateTime)

    user_id: Mapped[int] = mapped_column(Integer(), ForeignKey(User.id))
    user: Mapped[User] = relationship(User, backref="posts")

    def __repr__(self):
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
    admin.add_view(ModelView(User, db))
    admin.add_view(ModelView(Post, db))

    with app.app_context():
        db.create_all()

    app.run(debug=True)
