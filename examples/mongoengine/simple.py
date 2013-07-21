import datetime

from flask import Flask

from flask.ext import admin, wtf
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'
app.config['MONGODB_SETTINGS'] = {'DB': 'testing'}

# Create models
db = MongoEngine()
db.init_app(app)


# Define mongoengine documents
class User(db.Document):
    name = db.StringField(max_length=40)
    tags = db.ListField(db.ReferenceField('Tag'))
    password = db.StringField(max_length=40)

    def __unicode__(self):
        return self.name


class Todo(db.Document):
    title = db.StringField(max_length=60)
    text = db.StringField()
    done = db.BooleanField(default=False)
    pub_date = db.DateTimeField(default=datetime.datetime.now)
    user = db.ReferenceField(User)

    # Required for administrative interface
    def __unicode__(self):
        return self.title


class Tag(db.Document):
    name = db.StringField(max_length=10)

    def __unicode__(self):
        return self.name


class Comment(db.EmbeddedDocument):
    name = db.StringField(max_length=20)
    value = db.StringField(max_length=20)


class Post(db.Document):
    name = db.StringField(max_length=20)
    value = db.StringField(max_length=20)
    inner = db.ListField(db.EmbeddedDocumentField(Comment))
    lols = db.ListField(db.StringField(max_length=20))


class File(db.Document):
    name = db.StringField(max_length=20)
    data = db.FileField()


# Customized admin views
class UserView(ModelView):
    column_filters = ['name']

    column_searchable_list = ('name', 'password')


class TodoView(ModelView):
    column_filters = ['done']


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 'Simple Models')

    # Add views
    admin.add_view(UserView(User))
    admin.add_view(TodoView(Todo))
    admin.add_view(ModelView(Tag))
    admin.add_view(ModelView(Post))
    admin.add_view(ModelView(File))

    # Start app
    app.run(debug=True)
