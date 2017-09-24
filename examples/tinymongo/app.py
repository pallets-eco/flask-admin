"""
Example of Flask-Admin using TinyDB with TinyMongo
refer to README.txt for instructions

Author:  Bruno Rocha <@rochacbruno>
Based in PyMongo Example and TinyMongo
"""
import flask_admin as admin
from flask import Flask
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.form import Select2Widget
from flask_admin.model.fields import InlineFieldList, InlineFormField
from wtforms import fields, form

from tinymongo import TinyMongoClient

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create models in a JSON file localted at

DATAFOLDER = '/tmp/flask_admin_test'

conn = TinyMongoClient(DATAFOLDER)
db = conn.test

# create some users for testing
# for i in range(30):
#     db.user.insert({'name': 'Mike %s' % i})


# User admin
class InnerForm(form.Form):
    name = fields.StringField('Name')
    test = fields.StringField('Test')


class UserForm(form.Form):
    foo = fields.StringField('foo')
    name = fields.StringField('Name')
    email = fields.StringField('Email')
    password = fields.StringField('Password')

    # Inner form
    inner = InlineFormField(InnerForm)

    # Form list
    form_list = InlineFieldList(InlineFormField(InnerForm))


class UserView(ModelView):
    column_list = ('name', 'email', 'password', 'foo')
    column_sortable_list = ('name', 'email', 'password')

    form = UserForm

    page_size = 20
    can_set_page_size = True


# Tweet view
class TweetForm(form.Form):
    name = fields.StringField('Name')
    user_id = fields.SelectField('User', widget=Select2Widget())
    text = fields.StringField('Text')

    testie = fields.BooleanField('Test')


class TweetView(ModelView):
    column_list = ('name', 'user_name', 'text')
    column_sortable_list = ('name', 'text')

    column_filters = (filters.FilterEqual('name', 'Name'),
                      filters.FilterNotEqual('name', 'Name'),
                      filters.FilterLike('name', 'Name'),
                      filters.FilterNotLike('name', 'Name'),
                      filters.BooleanEqualFilter('testie', 'Testie'))

    # column_searchable_list = ('name', 'text')

    form = TweetForm

    def get_list(self, *args, **kwargs):
        count, data = super(TweetView, self).get_list(*args, **kwargs)

        # Contribute user_name to the models
        for item in data:
            item['user_name'] = db.user.find_one(
                {'_id': item['user_id']}
            )['name']

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
        model['user_id'] = user_id

        return model


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, name='Example: TinyMongo - TinyDB')

    # Add views
    admin.add_view(UserView(db.user, 'User'))
    admin.add_view(TweetView(db.tweet, 'Tweets'))

    # Start app
    app.run(debug=True)
