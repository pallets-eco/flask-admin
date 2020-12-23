
from flask import Flask
import flask_admin
from flask_admin.contrib import appengine
from google.cloud import ndb

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

admin = flask_admin.Admin(app, name="Admin")


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class House(ndb.Model):
    address = ndb.StringProperty()
    json_property = ndb.JsonProperty()
    indexed_int = ndb.IntegerProperty()
    unindexed_int = ndb.IntegerProperty(indexed=False)
    text_property = ndb.TextProperty()
    datetime_property = ndb.DateTimeProperty()


class Room(ndb.Model):
    house = ndb.KeyProperty(kind=House)
    name = ndb.StringProperty()


admin.add_view(appengine.ModelView(House))
admin.add_view(appengine.ModelView(Room))

if __name__ == '__main__':

    # Start app
    app.run(debug=True)
