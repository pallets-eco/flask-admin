from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext import admin, wtf
from flask.ext.admin.contrib.sqlamodel import ModelView

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dummy.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(64))

    def __unicode__(self):
        return self.name


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    text = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


# Customized admin interface
class CustomView(ModelView):
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'


class UserAdmin(CustomView):
    column_searchable_list = ('name',)
    column_filters = ('name', 'email')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin with custom base template
    admin = admin.Admin(app, base_template='layout.html')

    # Add views
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(CustomView(Page, db.session))

    # Create DB
    db.create_all()

    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
