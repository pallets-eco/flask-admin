from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
admin = Admin(
    app,
    name="Example: SQLAlchemy Association Proxy",
    theme=Bootstrap4Theme(),
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):  # type: ignore[name-defined]
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    # Association proxy of "user_keywords" collection to "keyword" attribute - a list
    # of keywords objects.
    keywords = association_proxy("user_keywords", "keyword")
    # Association proxy to association proxy - a list of keywords strings.
    keywords_values = association_proxy("user_keywords", "keyword_value")

    def __init__(self, name=None):
        self.name = name


class UserKeyword(db.Model):  # type: ignore[name-defined]
    __tablename__ = "user_keyword"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey("keyword.id"), primary_key=True)
    special_key = db.Column(db.String(50))

    # Bidirectional attribute/collection of "user"/"user_keywords"
    user = relationship(
        User, backref=backref("user_keywords", cascade="all, delete-orphan")
    )

    # Reference to the "Keyword" object
    keyword = relationship("Keyword")
    # Reference to the "keyword" column inside the "Keyword" object.
    keyword_value = association_proxy("keyword", "keyword")

    def __init__(self, keyword=None, user=None, special_key=None):
        self.user = user
        self.keyword = keyword
        self.special_key = special_key


class Keyword(db.Model):  # type: ignore[name-defined]
    __tablename__ = "keyword"
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column("keyword", db.String(64))

    def __init__(self, keyword=None):
        self.keyword = keyword

    def __repr__(self):
        return f"Keyword({repr(self.keyword)})"


class UserAdmin(ModelView):
    """Flask-admin can not automatically find a association_proxy yet. You will
    need to manually define the column in list_view/filters/sorting/etc.
    Moreover, support for association proxies to association proxies
    (e.g.: keywords_values) is currently limited to column_list only."""

    column_list = ("id", "name", "keywords", "keywords_values")
    column_sortable_list = ("id", "name")
    column_filters = ("id", "name", "keywords")
    form_columns = ("name", "keywords")


class KeywordAdmin(ModelView):
    column_list = ("id", "keyword")


if __name__ == "__main__":
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(KeywordAdmin(Keyword, db.session))

    with app.app_context():
        db.create_all()
        user = User("log")

        for kw in (Keyword("new_from_blammo"), Keyword("its_big")):
            user.keywords.append(kw)

        db.session.add(user)
        db.session.commit()

    app.run(debug=True)
