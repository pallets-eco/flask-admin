from bson import ObjectId
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.mongoengine import filters
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.form import Select2Widget
from flask_admin.model.fields import InlineFieldList
from flask_admin.model.fields import InlineFormField
from mongoengine import BooleanField
from mongoengine import connect
from mongoengine import Document
from mongoengine import EmbeddedDocument
from mongoengine import EmbeddedDocumentField
from mongoengine import EmbeddedDocumentListField
from mongoengine import ReferenceField
from mongoengine import StringField
from testcontainers.mongodb import MongoDbContainer
from wtforms import fields
from wtforms import form

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: MongoEngine")


class InnerForm(form.Form):
    name = fields.StringField("Name")
    test = fields.StringField("Test")


class Inner(EmbeddedDocument):
    name = StringField()
    test = StringField()


class User(Document):
    name = StringField()
    email = StringField()
    password = StringField()

    inner = EmbeddedDocumentField(Inner, default=Inner)
    form_list = EmbeddedDocumentListField(Inner, default=list)

    meta = {"collection": "user"}


class SafeInlineFieldList(InlineFieldList):
    """
    Prevent type error when InlineFieldList is assigned to an empty object.
    """

    def populate_obj(self, obj, name):
        # Get the current value or initialize as empty list
        values = getattr(obj, name, [])

        # Clear the existing list
        while values:
            values.pop()

        # Add new values from form data
        for entry in self.entries:
            if entry.data and any(entry.data.values()):  # Only add non-empty entries
                # Create a new embedded document
                embedded_doc = Inner()
                for field_name, field_value in entry.data.items():
                    if field_value:  # Only set non-empty values
                        setattr(embedded_doc, field_name, field_value)
                values.append(embedded_doc)


class UserForm(form.Form):
    name = fields.StringField("Name")
    email = fields.StringField("Email")
    password = fields.StringField("Password")

    # Inner form
    inner = InlineFormField(InnerForm)

    # Form list
    form_list = SafeInlineFieldList(InlineFormField(InnerForm))


class UserView(ModelView):
    column_list = ("name", "email", "password")
    column_sortable_list = ("name", "email", "password")

    form = UserForm


class Tweet(Document):
    name = StringField(required=True)
    user_id = ReferenceField(User, required=True)
    text = StringField(required=True)
    testie = BooleanField(default=False)
    meta = {"collection": "tweet"}


# Tweet view
class TweetForm(form.Form):
    name = fields.StringField("Name")
    user_id = fields.SelectField("User", widget=Select2Widget())
    text = fields.StringField("Text")

    testie = fields.BooleanField("Test")


class TweetView(ModelView):
    column_list = ("name", "user_name", "text")
    column_sortable_list = ("name", "text")

    column_filters = (
        filters.FilterEqual("name", "Name"),
        filters.FilterNotEqual("name", "Name"),
        filters.FilterLike("name", "Name"),
        filters.FilterNotLike("name", "Name"),
        filters.BooleanEqualFilter("testie", "Testie"),
    )

    column_searchable_list = ("name", "text")

    form = TweetForm

    def get_list(self, *args, **kwargs):
        count, data = super().get_list(*args, **kwargs)

        # Extract user IDs from tweets
        user_ids = [tweet.user_id.id if tweet.user_id else None for tweet in data]
        user_ids = list(filter(None, user_ids))  # Remove None values

        # Fetch user names by IDs
        users = User.objects(id__in=user_ids).only("name")
        users_map = {user.id: user.name for user in users}

        # Add user_name attribute for display
        for tweet in data:
            tweet.user_name = users_map.get(tweet.user_id.id if tweet.user_id else None)

        return count, data

    # Contribute list of user choices to the forms
    def _feed_user_choices(self, form):
        users = User.objects.only("name")
        form.user_id.choices = [(str(user.id), user.name) for user in users]
        return form

    def create_form(self, obj=None):
        form = super().create_form(obj)
        return self._feed_user_choices(form)

    def edit_form(self, obj):  # type: ignore[override]
        form = super().edit_form(obj)
        return self._feed_user_choices(form)

    def on_model_change(self, form, model, is_created):
        if isinstance(model.user_id, str):
            model.user_id = ObjectId(model.user_id)
        return super().on_model_change(form, model, is_created)


# Flask views
@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == "__main__":
    with MongoDbContainer("mongo:7.0.7") as mongo:
        mongo_uri = mongo.get_connection_url()
        connect(host=mongo_uri)

        admin.add_view(UserView(User, "User"))
        admin.add_view(TweetView(Tweet, "Tweets"))

        app.run(debug=True)
