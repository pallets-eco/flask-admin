import datetime
import os
import random

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import Select2Field
from flask_admin.theme import Bootstrap5Theme
from flask_sqlalchemy import SQLAlchemy
from wtforms.fields import DateTimeLocalField


# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config["SECRET_KEY"] = "123456790"

# Create in-memory database
app.config["DATABASE_FILE"] = "sample_db.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    organization_id = db.Column(
        db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('Organization', back_populates='users')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    shortname = db.Column(db.Unicode(16))

    users = db.relationship('User', back_populates='organization')

    def __unicode__(self):
        return f"{self.name} {self.shortname}"

    def __repr__(self):
        return self.shortname


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(64))
    content = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


# Customized admin interface
class CustomView(ModelView):
    pass


class UserAdmin(CustomView):
    column_searchable_list = ("name",)
    column_filters = ("name", "email", "organization", "active")
    can_export = True
    export_types = ["csv", "xlsx"]

    form_columns = ['name', 'email', 'active', 'organization_id']

    form_overrides = {
        'organization_id': Select2Field,
        'created_at': DateTimeLocalField
    }

    form_args = {
        'organization_id': {
            'choices': [],
            'coerce': int,
            'label': 'Organization',
            'description': 'select an organization for this user'
        }
    }

    can_view_details = True
    details_modal = True
    create_modal = True
    edit_modal = True

    def _organization_id_choices(self):
        return [
            (o.id, f"{o.name} ({o.shortname})")
            for o in Organization.query.all()
        ]

    def make_form(self, create_or_edit_form, obj=None):
        form = create_or_edit_form(obj)
        form.organization_id.choices = self._organization_id_choices()
        return form

    def create_form(self, obj=None):
        return self.make_form(super().create_form, obj)

    def edit_form(self, obj=None):
        return self.make_form(super().edit_form, obj)


class OrganizationAdmin(CustomView):
    column_searchable_list = ("name", "shortname")
    column_filters = ("name", "shortname")
    create_modal = True

    inline_models = [User, ]

    can_view_details = True


# Flask views
@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create admin with custom base template
admin = Admin(app, "Example: Bootstrap5",
              theme=Bootstrap5Theme(swatch="default", fluid=True))

# Add views
admin.add_view(UserAdmin(User, db.session, category="Menu"))
admin.add_view(OrganizationAdmin(Organization, db.session, category="Menu"))

admin.add_sub_category(name="Submenu", parent_name="Menu")
admin.add_view(CustomView(Page, db.session, category="Submenu"))


def build_sample_db():
    """
    Populate a small db with some example entries.
    This version creates multiple organizations and randomly assigns them to users.
    """

    # Drop all existing tables and recreate them from the models
    db.drop_all()
    db.create_all()

    # Define the data for multiple dummy organizations
    organizations_data = [
        {"name": "ACME Corporation", "shortname": "ACME"},
        {"name": "Stark Industries", "shortname": "Stark"},
        {"name": "Wayne Enterprises", "shortname": "Wayne"},
        {"name": "Globex Corporation", "shortname": "Globex"},
        {"name": "Cyberdyne Systems", "shortname": "Cyberdyne"},
    ]

    # This list will hold the created Organization objects
    organizations = []

    # Create Organization objects and add them to the database
    for org_data in organizations_data:
        organization = Organization(
            name=org_data["name"], shortname=org_data["shortname"])
        db.session.add(organization)
        organizations.append(organization)

    # Sample data for creating users
    first_names = [
        "Harry", "Amelia", "Oliver", "Jack", "Isabella", "Charlie", "Sophie",
        "Mia", "Jacob", "Thomas", "Emily", "Lily", "Ava", "Isla", "Alfie",
        "Olivia", "Jessica", "Riley", "William", "James", "Geoffrey", "Lisa",
        "Benjamin", "Stacey", "Lucy",
    ]
    last_names = [
        "Brown", "Smith", "Patel", "Jones", "Williams", "Johnson", "Taylor",
        "Thomas", "Roberts", "Khan", "Lewis", "Jackson", "Clarke", "James",
        "Phillips", "Wilson", "Ali", "Mason", "Mitchell", "Rose", "Davis",
        "Davies", "Rodriguez", "Cox", "Alexander",
    ]

    # Create users and assign a random organization to each one
    for i in range(len(first_names)):
        user = User()
        user.name = f"{first_names[i]} {last_names[i]}"
        user.email = f"{first_names[i].lower()}@example.com"

        # Pick a random organization from the list created above
        user.organization = random.choice(organizations)

        db.session.add(user)

    # Sample data for creating pages
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

    # Create Page objects and add them to the database
    for entry in sample_text:
        page = Page()
        page.title = entry["title"]
        page.content = entry["content"]
        db.session.add(page)

    # Commit all the changes to the database
    db.session.commit()

    return


if __name__ == "__main__":
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    # Start app
    app.run(debug=True, host="0.0.0.0")
