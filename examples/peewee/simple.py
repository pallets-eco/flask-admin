from flask import Flask

import peewee

from flask.ext import admin
from flask.ext.admin.contrib import peeweemodel


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


class Post(BaseModel):
    title = peewee.CharField(max_length=120)
    text = peewee.TextField(null=False)
    date = peewee.DateTimeField()

    user = peewee.ForeignKeyField(User)

    def __unicode__(self):
        return self.title


class PostAdmin(peeweemodel.ModelView):
    # Visible columns in the list view
    #list_columns = ('title', 'user')
    excluded_list_columns = ['text']

    # List of columns that can be sorted. For 'user' column, use User.username as
    # a column.
    #sortable_columns = ('title', ('user', User.username), 'date')

    searchable_columns = ('title', User.username)

    column_filters = ('title',
                      'date',
                      User.username)


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    admin = admin.Admin(app, 'Peewee Models')

    admin.add_view(peeweemodel.ModelView(User))
    admin.add_view(PostAdmin(Post))

    try:
        User.create_table()
        Post.create_table()
    except:
        pass

    app.debug = True
    app.run('0.0.0.0', 8000)
