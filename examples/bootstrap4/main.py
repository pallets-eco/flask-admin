import datetime
import os.path as op

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.model.template import LinkRowAction
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["DATABASE_FILE"] = "db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
admin = Admin(
    app,
    name="Example: Bootstrap4",
    theme=Bootstrap4Theme(swatch="flatly"),
    category_icon_classes={
        "Menu": "fa fa-cog text-danger",
    },
)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __unicode__(self):
        return self.name


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(64))
    content = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


class CustomView(ModelView):
    column_extra_row_actions = [
        LinkRowAction("bi bi-chat-quote", "/admin/page?id={row_id}"),
        EndpointLinkRowAction("bi bi-cake-fill", ".index_view"),
    ]


class UserAdmin(CustomView):
    column_searchable_list = ("name",)
    column_filters = ("name", "email")
    can_export = True
    export_types = ["csv", "xlsx"]
    can_set_page_size = True
    page_size_options = (3, 5, 7, 10, 20, 50, 100)
    page_size = 7


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    db.drop_all()
    db.create_all()

    first_names = [
        "Harry",
        "Amelia",
        "Oliver",
        "Jack",
        "Isabella",
        "Charlie",
        "Sophie",
        "Mia",
        "Jacob",
        "Thomas",
        "Emily",
        "Lily",
        "Ava",
        "Isla",
        "Alfie",
        "Olivia",
        "Jessica",
        "Riley",
        "William",
        "James",
        "Geoffrey",
        "Lisa",
        "Benjamin",
        "Stacey",
        "Lucy",
    ]
    last_names = [
        "Brown",
        "Smith",
        "Patel",
        "Jones",
        "Williams",
        "Johnson",
        "Taylor",
        "Thomas",
        "Roberts",
        "Khan",
        "Lewis",
        "Jackson",
        "Clarke",
        "James",
        "Phillips",
        "Wilson",
        "Ali",
        "Mason",
        "Mitchell",
        "Rose",
        "Davis",
        "Davies",
        "Rodriguez",
        "Cox",
        "Alexander",
    ]

    for i in range(len(first_names)):
        user = User()
        user.name = first_names[i] + " " + last_names[i]
        user.email = first_names[i].lower() + "@example.com"
        db.session.add(user)

    sample_text = [
        {
            "title": "de Finibus Bonorum et Malorum - Part I",
            "content": (
                "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do "
                "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
                "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
                "aliquip ex ea commodo consequat. Duis aute irure dolor in "
                "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
                "culpa qui officia deserunt mollit anim id est laborum."
            ),
        },
        {
            "title": "de Finibus Bonorum et Malorum - Part II",
            "content": (
                "Sed ut perspiciatis unde omnis iste natus error sit voluptatem "
                "accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae "
                "ab illo inventore veritatis et quasi architecto beatae vitae dicta "
                "sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit "
                "aspernatur aut odit aut fugit, sed quia consequuntur magni dolores "
                "eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, "
                "qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, "
                "sed quia non numquam eius modi tempora incidunt ut labore et dolore "
                "magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis "
                "nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut "
                "aliquid ex ea commodi consequatur? Quis autem vel eum iure "
                "reprehenderit qui in ea voluptate velit esse quam nihil molestiae "
                "consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla "
                "pariatur?"
            ),
        },
        {
            "title": "de Finibus Bonorum et Malorum - Part III",
            "content": (
                "At vero eos et accusamus et iusto odio dignissimos ducimus qui "
                "blanditiis praesentium voluptatum deleniti atque corrupti quos "
                "dolores et quas molestias excepturi sint occaecati cupiditate non "
                "provident, similique sunt in culpa qui officia deserunt mollitia "
                "animi, id est laborum et dolorum fuga. Et harum quidem rerum "
                "facilis est et expedita distinctio. Nam libero tempore, cum soluta "
                "nobis est eligendi optio cumque nihil impedit quo minus id quod "
                "maxime placeat facere possimus, omnis voluptas assumenda est, omnis "
                "dolor repellendus. Temporibus autem quibusdam et aut officiis debitis "
                "aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae "
                "sint et molestiae non recusandae. Itaque earum rerum hic tenetur a "
                "sapiente delectus, ut aut reiciendis voluptatibus maiores alias "
                "consequatur aut perferendis doloribus asperiores repellat."
            ),
        },
    ]

    for entry in sample_text:
        page = Page()
        page.title = entry["title"]
        page.content = entry["content"]
        db.session.add(page)

    db.session.commit()
    return


if __name__ == "__main__":
    # Icons reference (FontAwesome v4):
    # https://fontawesome.com/v4/icons/

    admin.add_view(
        UserAdmin(
            User,
            db.session,
            category="Menu",
            menu_icon_type="fa",
            menu_icon_value="fa-users",
            menu_class_name="text-warning",
        )
    )
    admin.add_view(CustomView(Page, db.session, category="Menu"))
    admin.add_view(
        CustomView(
            Page,
            db.session,
            name="Page-with-icon",
            endpoint="page2",
            menu_class_name="text-danger",
            menu_icon_type="fa",
            menu_icon_value="fa-file",
        )
    )

    admin.add_link(
        MenuLink(
            name="link1",
            url="http://www.example.com/",
            class_name="text-warning bg-danger",
            icon_type="fa",
            icon_value="fa-external-link",
        )
    )
    admin.add_link(
        MenuLink(name="link2", url="http://www.example.com/", class_name="text-danger")
    )
    admin.add_link(MenuLink(name="Link3", url="http://www.example.com/"))

    admin.add_sub_category(name="Links", parent_name="Menu")
    admin.add_link(
        MenuLink(
            name="External link",
            url="http://www.example.com/",
            category="Links",
            class_name="text-info",
            icon_type="fa",
            icon_value="fa-external-link",
        )
    )
    admin.add_link(
        MenuLink(
            name="External link",
            url="http://www.example.com/",
            category="Links",
            class_name="text-success",
        )
    )
    admin.add_link(
        MenuLink(name="External link", url="http://www.example.com/", category="Links")
    )

    admin.add_link(
        MenuLink(
            name="Fontawesome",
            url="http://www.example.com/",
            category="Icons",
            icon_type="fa",
            icon_value="fa-home shadow",
        )
    )
    admin.add_link(
        MenuLink(
            name="Bootstrap Icons",
            url="http://www.example.com/",
            category="Icons",
            icon_type="bi",
            icon_value="bi-bootstrap",
        )
    )
    admin.add_link(
        MenuLink(
            name="glyphicon",
            url="http://www.example.com/",
            category="Icons",
            icon_type="glyph",
            icon_value="glyphicon-home",
        )
    )
    admin.add_link(
        MenuLink(
            name="image from /static",
            url="http://www.example.com/",
            category="Icons",
            icon_type="image",
            icon_value="h.png",
            class_name="shadow",
        )
    )
    admin.add_link(
        MenuLink(
            name="image URL",
            url="http://www.example.com/",
            category="Icons",
            icon_type="image-url",
            icon_value="https://placehold.co/32?text=S",
        )
    )

    admin.add_sub_category("Links", parent_name="Icons")
    admin.add_link(
        MenuLink(name="External Link1", url="https://example.com/", category="Links")
    )
    admin.add_link(
        MenuLink(name="External Link2", url="https://example.com/", category="Links")
    )

    app_dir = op.realpath(op.dirname(__file__))
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not op.exists(database_path):
        with app.app_context():
            build_sample_db()

    app.run(debug=True)
