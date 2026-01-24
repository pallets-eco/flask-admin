import os
import os.path as op

from flask import Flask
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from examples.custom_layout.data import first_names
from examples.custom_layout.data import last_names
from examples.custom_layout.data import sample_text

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = False
db = SQLAlchemy(app)


class MyHomeView(AdminIndexView):
    @expose("/")
    def index(self):
        user_count = db.session.scalar(select(func.count()).select_from(User))
        pages_count = db.session.scalar(select(func.count()).select_from(Page))
        sales_sum = db.session.scalar(select(func.sum(Sale.amount))) or 0
        return self.render(
            "admin/index.html",
            user_count=user_count,
            pages_count=pages_count,
            sales_sum=round(sales_sum, 2),
        )


# 2. Pass this view to the Admin object
admin = Admin(
    app,
    name="Example: Custom Layout",
    index_view=MyHomeView(),
    theme=Bootstrap4Theme(base_template="admin/custom_layout.html"),
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(64))

    def __repr__(self):
        return self.name


class Page(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64))
    content: Mapped[Text] = mapped_column(Text)

    def __repr__(self):
        return self.name


class Sale(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item: Mapped[str] = mapped_column(String(64))
    amount: Mapped[int] = mapped_column(Numeric)

    def __repr__(self):
        return self.item


class CustomView(ModelView):
    list_template = "list.html"
    create_template = "create.html"
    edit_template = "edit.html"


class UserAdmin(CustomView):
    column_searchable_list = ("name",)
    column_filters = ("name", "email")


def build_sample_db(names, surnames, pages):
    """
    Populate a small db with some example entries.
    """
    db.drop_all()
    db.create_all()
    db.session.add_all(
        User(
            name=f"{name} {surname}",
            email=f"{name.lower()}.{surname.lower()}@example.com",
        )
        for name, surname in zip(names, surnames, strict=False)
    )
    db.session.add_all(
        Page(title=entry["title"], content=entry["content"]) for entry in pages
    )
    db.session.add(Sale(item="Sample Item 1", amount=19.99))
    db.session.commit()


if __name__ == "__main__":
    admin.add_view(UserAdmin(User, db))
    admin.add_view(CustomView(Page, db))
    admin.add_view(CustomView(Sale, db))

    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db(first_names, last_names, sample_text)

    app.run(debug=True)
