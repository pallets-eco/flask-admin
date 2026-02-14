from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import backref
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["SQLALCHEMY_ECHO"] = False
db = SQLAlchemy(app)
admin = Admin(
    app,
    name="Example: SQLAlchemy Association Proxy",
    theme=Bootstrap4Theme(),
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))

    # Association proxy of "user_keywords" collection to "keyword" attribute - a list
    # of keywords objects.
    keywords: AssociationProxy[list[str]] = association_proxy(
        "user_keywords", "keyword"
    )
    # Association proxy to association proxy - a list of keywords strings.
    keywords_values: AssociationProxy[list[str]] = association_proxy(
        "user_keywords", "keyword_value"
    )

    def __init__(self, name=None):
        self.name = name


class UserKeyword(db.Model):
    __tablename__ = "user_keyword"
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keyword.id"), primary_key=True
    )
    special_key: Mapped[str] = mapped_column(String(50), nullable=True)

    # Bidirectional attribute/collection of "user"/"user_keywords"
    user: Mapped[User] = relationship(
        User, backref=backref("user_keywords", cascade="all, delete-orphan")
    )

    # Reference to the "Keyword" object
    keyword: Mapped["Keyword"] = relationship("Keyword")
    # Reference to the "keyword" column inside the "Keyword" object.
    keyword_value: AssociationProxy[list[str]] = association_proxy("keyword", "keyword")

    def __init__(self, keyword=None, user=None, special_key=None):
        self.user = user
        self.keyword = keyword
        self.special_key = special_key


class Keyword(db.Model):
    __tablename__ = "keyword"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column("keyword", String(64))

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
    admin.add_view(UserAdmin(User, db))
    admin.add_view(KeywordAdmin(Keyword, db))

    with app.app_context():
        db.create_all()
        user = User("log")

        for kw in (Keyword("new_from_blammo"), Keyword("its_big")):
            user.keywords.append(kw)

        db.session.add(user)
        db.session.commit()

    app.run(debug=True)
