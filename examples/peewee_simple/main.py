import uuid

import peewee
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.peewee import ModelView
from peewee import CharField
from peewee import Model
from peewee import SqliteDatabase

app = Flask(__name__)
app.config["SECRET_KEY"] = "123456790"

db = SqliteDatabase("db.sqlite", check_same_thread=False)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(max_length=80)
    email = CharField(max_length=120)

    def __str__(self):
        return self.username


class UserInfo(BaseModel):
    key = CharField(max_length=64)
    value = CharField(max_length=64)

    user = peewee.ForeignKeyField(User)

    def __str__(self):
        return f"{self.key} - {self.value}"


class Post(BaseModel):
    id = peewee.UUIDField(primary_key=True, default=uuid.uuid4)
    title = CharField(max_length=120)
    text = peewee.TextField(null=False)
    date = peewee.DateTimeField()

    user = peewee.ForeignKeyField(User)

    def __str__(self):
        return self.title


class UserAdmin(ModelView):
    inline_models = (UserInfo,)


class PostAdmin(ModelView):
    # Visible columns in the list view
    column_exclude_list = ["text"]

    # List of columns that can be sorted. For 'user' column, use User.email as
    # a column.
    # column_sortable_list = ("title", ("user", User.email), "date")
    column_sortable_list = ("name", ("user", ("user.first_name", "user.last_name")))

    # Full text search
    column_searchable_list = ("title", User.username)

    # Column filters
    column_filters = ("title", "date", User.username)

    form_ajax_refs = {"user": {"fields": (User.username, "email")}}


class Book(BaseModel):
    isbn = CharField(max_length=13, primary_key=True)
    name = CharField(max_length=120)


class Category(BaseModel):
    id = peewee.AutoField(primary_key=True)
    name = CharField(unique=True, max_length=50)


# broken many-to-many model
class BookCategory(BaseModel):
    id = peewee.AutoField()  # Surrogate key
    isbn = peewee.ForeignKeyField(
        Book,
        # column_name='isbn',
        backref="book_categories",
    )
    category = peewee.ForeignKeyField(
        Category,
        # column_name='category'
        backref="category",
    )

    class Meta:
        db_table = "books_categories"
        indexes = ((("isbn", "category"), True),)


class ViewWithPk(ModelView):
    column_display_pk = True
    form_columns = [
        "isbn",
        "name",
        "category",
    ]


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    admin = Admin(app, name="Example: Peewee")

    admin.add_view(UserAdmin(User))
    admin.add_view(PostAdmin(Post))

    admin.add_view(ViewWithPk(Book))
    admin.add_view(ModelView(Category))
    admin.add_view(ViewWithPk(BookCategory))

    # Create tables first
    with db:
        db.drop_tables([BookCategory, Post, UserInfo, Book, Category, User], safe=True)
        db.create_tables(
            [User, UserInfo, Post, Book, Category, BookCategory], safe=True
        )
    with db.atomic():
        # Create sample books
        book1, created = Book.get_or_create(
            isbn="111", defaults={"name": "Sample Book 1"}
        )
        book2, created = Book.get_or_create(
            isbn="222", defaults={"name": "Sample Book 2"}
        )

        # Create sample categories
        cat1, created = Category.get_or_create(name="Fiction")
        cat2, created = Category.get_or_create(name="Science")

        # Create relationships
        BookCategory.get_or_create(isbn=book1, category=cat1)
        BookCategory.get_or_create(isbn=book2, category=cat2)

    app.run(debug=True)
