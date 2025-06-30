"""
Example of Flask-Admin using TinyDB with TinyMongo
refer to README.txt for instructions

Author:  Bruno Rocha <@rochacbruno>
Based in PyMongo Example and TinyMongo
"""

import tinydb
import tinymongo as tm
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.pymongo import ModelView
from flask_admin.contrib.pymongo.filters import BooleanEqualFilter
from flask_admin.contrib.pymongo.filters import FilterEqual
from flask_admin.contrib.pymongo.filters import FilterLike
from flask_admin.contrib.pymongo.filters import FilterNotEqual
from flask_admin.contrib.pymongo.filters import FilterNotLike
from flask_admin.form import Select2Widget
from flask_admin.model.fields import InlineFieldList
from flask_admin.model.fields import InlineFormField
from wtforms import BooleanField
from wtforms import form
from wtforms import SelectField
from wtforms import StringField


# Taken from: [Error when loading database file · Issue #58 · schapman1974/tinymongo](https://github.com/schapman1974/tinymongo/issues/58)
class TinyMongoClient(tm.TinyMongoClient):
    @property
    def _storage(self):
        return tinydb.storages.JSONStorage


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: TinyMongo - TinyDB")

# Create models in a JSON file located at
conn = TinyMongoClient("/tmp/flask_admin_test")
db = conn.test


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class InnerForm(form.Form):
    name = StringField("Name")
    test = StringField("Test")


class UserForm(form.Form):
    foo = StringField("foo")
    name = StringField("Name")
    email = StringField("Email")
    password = StringField("Password")
    inner = InlineFormField(InnerForm)
    form_list = InlineFieldList(InlineFormField(InnerForm))


class UserView(ModelView):
    column_list = ("name", "email", "password", "foo")
    column_sortable_list = ("name", "email", "password")

    form = UserForm

    page_size = 20
    can_set_page_size = True


class TweetForm(form.Form):
    name = StringField("Name")
    user_id = SelectField("User", widget=Select2Widget())
    text = StringField("Text")

    testie = BooleanField("Test")


class TweetView(ModelView):
    column_list = ("name", "user_name", "text")
    column_sortable_list = ("name", "text")

    column_filters = (
        FilterEqual("name", "Name"),
        FilterNotEqual("name", "Name"),
        FilterLike("name", "Name"),
        FilterNotLike("name", "Name"),
        BooleanEqualFilter("testie", "Testie"),
    )

    # column_searchable_list = ('name', 'text')

    form = TweetForm

    def get_list(self, *args, **kwargs):
        count, data = super().get_list(*args, **kwargs)

        # Contribute user_name to the models
        for item in data:
            item["user_name"] = db.user.find_one({"_id": item["user_id"]})["name"]

        return count, data

    # Contribute list of user choices to the forms
    def _feed_user_choices(self, form):
        users = db.user.find(fields=("name",))
        form.user_id.choices = [(str(x["_id"]), x["name"]) for x in users]
        return form

    def create_form(self):
        form = super().create_form()
        return self._feed_user_choices(form)

    def edit_form(self, obj):
        form = super().edit_form(obj)
        return self._feed_user_choices(form)

    # Correct user_id reference before saving
    def on_model_change(self, form, model):
        user_id = model.get("user_id")
        model["user_id"] = user_id
        return model


if __name__ == "__main__":
    """
    # Seed the database for convenience
    for i in range(30):
        db.user.insert({'name': 'Mike %s' % i})
    """
    # TODO @hasansezertasan: This example is not working...
    admin.add_view(UserView(db.user, "User"))
    admin.add_view(TweetView(db.tweet, "Tweets"))
    app.run(debug=True)
