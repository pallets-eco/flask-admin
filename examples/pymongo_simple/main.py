from typing import Any

from bson.objectid import ObjectId
from flask import Flask
from flask import url_for
from flask_admin import Admin
from flask_admin.contrib.pymongo import filters
from flask_admin.contrib.pymongo import ModelView
from flask_admin.form import Select2Widget
from flask_admin.model.fields import InlineFieldList
from flask_admin.model.fields import InlineFormField
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer
from wtforms import fields
from wtforms import form

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: PyMongo")


class InnerForm(form.Form):
    name = fields.StringField("Name")
    test = fields.StringField("Test")


class UserForm(form.Form):
    name = fields.StringField("Name")
    email = fields.StringField("Email")
    password = fields.StringField("Password")

    inner = InlineFormField(InnerForm)

    form_list = InlineFieldList(InlineFormField(InnerForm))


class UserView(ModelView):
    column_list = ("name", "email", "password")
    column_sortable_list = ("name", "email", "password")

    form = UserForm


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

        # Grab user names
        query = {"_id": {"$in": [x["user_id"] for x in data]}}
        users = db.user.find(query, projection=("name",))

        # Contribute user names to the models
        users_map = dict((x["_id"], x["name"]) for x in users)

        for item in data:
            item["user_name"] = users_map.get(item["user_id"])

        return count, data

    # Contribute list of user choices to the forms
    def _feed_user_choices(self, form):
        users = db.user.find(projection=("name",))
        form.user_id.choices = [(str(x["_id"]), x["name"]) for x in users]
        return form

    def create_form(self):  # type: ignore[override]
        form = super().create_form()
        return self._feed_user_choices(form)

    def edit_form(self, obj):  # type: ignore[override]
        form = super().edit_form(obj)
        return self._feed_user_choices(form)

    # Correct user_id reference before saving
    def on_model_change(self, form, model, is_created):
        user_id = model.get("user_id")
        model["user_id"] = ObjectId(user_id)

        return model


@app.route("/")
def index():
    return f'<a href="{url_for("admin.index")}">Go to admin!</a>'


if __name__ == "__main__":
    with MongoDbContainer("mongo:7.0.7") as mongo:
        conn: MongoClient[Any] = MongoClient(mongo.get_connection_url())
        db = conn.test

        admin.add_view(UserView(db.user, "User"))
        admin.add_view(TweetView(db.tweet, "Tweets"))

        app.run(debug=True)
