import pymongo
from bson.objectid import ObjectId

from flask import Flask

from flask.ext import admin, wtf

from flask.ext.admin.form import Select2Widget
from flask.ext.admin.contrib.pymongo import ModelView, filters
from flask.ext.admin.model import fields

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create models
conn = pymongo.Connection()
db = conn.test


# User admin
class InnerForm(wtf.Form):
    name = wtf.TextField('Name')
    test = wtf.TextField('Test')


class UserForm(wtf.Form):
    name = wtf.TextField('Name')
    email = wtf.TextField('Email')
    password = wtf.TextField('Password')

    # Inner form
    inner = fields.InlineFormField(InnerForm)

    # Form list
    form_list = fields.InlineFieldList(fields.InlineFormField(InnerForm))


class UserView(ModelView):
    list_columns = ('name', 'email', 'password')
    sortable_columns = ('name', 'email', 'password')

    form = UserForm


# Tweet view
class TweetForm(wtf.Form):
    name = wtf.TextField('Name')
    user_id = wtf.SelectField('User', widget=Select2Widget())
    text = wtf.TextField('Text')


class TweetView(ModelView):
    list_columns = ('name', 'user_name', 'text')
    sortable_columns = ('name', 'text')

    column_filters = (filters.FilterEqual('name', 'Name'),
                      filters.FilterNotEqual('name', 'Name'),
                      filters.FilterLike('name', 'Name'),
                      filters.FilterNotLike('name', 'Name'))

    searchable_columns = ('name', 'text')

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

        if isinstance(user_id, basestring):
            model['user_id'] = ObjectId(user_id)

        return model


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 'Simple Models')

    # Add views
    admin.add_view(UserView(db.user, 'User'))
    admin.add_view(TweetView(db.tweet, 'Tweets'))

    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
