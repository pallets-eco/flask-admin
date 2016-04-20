from flask import Flask

import peewee

import flask_admin as admin
from flask_admin.contrib.peewee import ModelView


app = Flask(__name__)
app.config['SECRET_KEY'] = '123456790'

db = peewee.SqliteDatabase('test.sqlite', check_same_thread=False)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    username = peewee.CharField(max_length=80)
    email = peewee.CharField(max_length=120)

    def __unicode__(self):
        return self.username


class UserInfo(BaseModel):
    key = peewee.CharField(max_length=64)
    value = peewee.CharField(max_length=64)

    user = peewee.ForeignKeyField(User)

    def __unicode__(self):
        return '%s - %s' % (self.key, self.value)


class Post(BaseModel):
    title = peewee.CharField(max_length=120)
    text = peewee.TextField(null=False)
    date = peewee.DateTimeField()

    user = peewee.ForeignKeyField(User)

    def __unicode__(self):
        return self.title


class UserAdmin(ModelView):
    inline_models = (UserInfo,)


class PostAdmin(ModelView):
    # Visible columns in the list view
    column_exclude_list = ['text']

    # List of columns that can be sorted. For 'user' column, use User.email as
    # a column.
    column_sortable_list = ('title', ('user', User.email), 'date')

    # Full text search
    column_searchable_list = ('title', User.username)

    # Column filters
    column_filters = ('title',
                      'date',
                      User.username)

    form_ajax_refs = {
        'user': {
            'fields': (User.username, 'email')
        }
    }


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    admin = admin.Admin(app, name='Example: Peewee')

    admin.add_view(UserAdmin(User))
    admin.add_view(PostAdmin(Post))

    try:
        User.create_table()
        UserInfo.create_table()
        Post.create_table()
    except:
        pass

    app.run(debug=True)
