from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from wtforms import fields, widgets

from flask.ext import admin
from flask.ext.admin.contrib import sqla

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dummy.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Define wtforms widget and field
class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(fields.TextAreaField):
    widget = CKTextAreaWidget()


# Model
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    text = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


# Customized admin interface
class PageAdmin(sqla.ModelView):
    form_overrides = dict(text=CKTextAreaField)

    create_template = 'create.html'
    edit_template = 'edit.html'


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app)

    # Add views
    admin.add_view(PageAdmin(Page, db.session))

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
