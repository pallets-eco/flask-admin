import datetime

from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib import mongoengine

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'
app.config['MONGODB_SETTINGS'] = {'DB': 'testing'}

# Create models
db = MongoEngine()
db.init_app(app)


class Todo(db.Document):
    title = db.StringField(max_length=60)
    text = db.StringField()
    done = db.BooleanField(default=False)
    pub_date = db.DateTimeField(default=datetime.datetime.now)

    # Required for administrative interface
    def __unicode__(self):
        return self.title


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 'Simple Models')

    # Add views
    admin.add_view(mongoengine.ModelView(Todo))

    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
