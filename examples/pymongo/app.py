import pymongo
from bson.objectid import ObjectId

from flask import Flask
import flask_admin as admin

from wtforms import form, fields

from flask_admin.form import Select2Widget
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.model.fields import InlineFormField, InlineFieldList

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create models
conn = pymongo.Connection()
db = conn.test


# User admin
class InnerForm(form.Form):
    name = fields.TextField('Name')
    test = fields.TextField('Test')


class UserForm(form.Form):
    name = fields.TextField('Name')
    email = fields.TextField('Email')
    password = fields.TextField('Password')

    # Inner form
    inner = InlineFormField(InnerForm)

    # Form list
    form_list = InlineFieldList(InlineFormField(InnerForm))


class UserView(ModelView):
    column_list = ('name', 'email', 'password')
    column_sortable_list = ('name', 'email', 'password')

    form = UserForm


# Tweet view
class TweetForm(form.Form):
    name = fields.TextField('Name')
    user_id = fields.SelectField('User', widget=Select2Widget())
    text = fields.TextField('Text')

    testie = fields.BooleanField('Test')


class TweetView(ModelView):
    column_list = ('name', 'user_name', 'text')
    column_sortable_list = ('name', 'text')

    column_filters = (filters.FilterEqual('name', 'Name'),
                      filters.FilterNotEqual('name', 'Name'),
                      filters.FilterLike('name', 'Name'),
                      filters.FilterNotLike('name', 'Name'),
                      filters.BooleanEqualFilter('testie', 'Testie'))

    column_searchable_list = ('name', 'text')

    form = TweetForm

    def get_list(self, *args, **kwargs):
        count, data = super(TweetView, self).get_list(*args, **kwargs)

        # Grab user names
        query = {'_id': {'$in': [x['user_id'] for x in data]}}
        users = db.user.find(query, fields=('name',))

        # Contribute user names to the models
        users_map = dict((x['_id'], x['name']) for x in users)

        for item in data:
            item['user_name'] = users_map.get(item['user_id'])

        return count, data

    # Contribute list of user choices to the forms
    def _feed_user_choices(self, form):
        users = db.user.find(fields=('name',))
        form.user_id.choices = [(str(x['_id']), x['name']) for x in users]
        return form

    def create_form(self):
        form = super(TweetView, self).create_form()
        return self._feed_user_choices(form)

    def edit_form(self, obj):
        form = super(TweetView, self).edit_form(obj)
        return self._feed_user_choices(form)

    # Correct user_id reference before saving
    def on_model_change(self, form, model):
        user_id = model.get('user_id')
        model['user_id'] = ObjectId(user_id)

        return model


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, name='Example: PyMongo')

    # Add views
    admin.add_view(UserView(db.user, 'User'))
    admin.add_view(TweetView(db.tweet, 'Tweets'))

    # Start app
    app.run(debug=True)
