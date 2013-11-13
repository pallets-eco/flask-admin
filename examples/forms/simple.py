import os
import os.path as op

from flask import Flask, url_for
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy.event import listens_for
from jinja2 import Markup

from flask.ext.admin import Admin, form
from flask.ext.admin.form import rules
from flask.ext.admin.contrib import sqla


# Create application
app = Flask(__name__, static_folder='files')

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), 'files')
try:
    os.mkdir(file_path)
except OSError:
    pass


# Create models
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    path = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.name


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    path = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.name


class RuleSample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Unicode(64))
    last_name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(128))
    phone = db.Column(db.Unicode(32))

    address = db.Column(db.Unicode(128))
    city = db.Column(db.Unicode(128))
    zip = db.Column(db.Unicode(8))

    notes = db.Column(db.UnicodeText)


# Delete hooks for models, delete files if models are getting deleted
@listens_for(File, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            # Don't care if was not deleted because it does not exist
            pass


@listens_for(Image, 'after_delete')
def del_image(mapper, connection, target):
    if target.path:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path,
                              form.thumbgen_filename(target.path)))
        except OSError:
            pass


# Administrative views
class FileView(sqla.ModelView):
    # Override form field to use Flask-Admin FileUploadField
    form_overrides = {
        'path': form.FileUploadField
    }

    # Pass additional parameters to 'path' to FileUploadField constructor
    form_args = {
        'path': {
            'label': 'File',
            'base_path': file_path
        }
    }


class ImageView(sqla.ModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''

        return Markup('<img src="%s">' % url_for('static',
                                                 filename=form.thumbgen_filename(model.path)))

    column_formatters = {
        'path': _list_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'path': form.ImageUploadField('Image',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }


class RuleView(sqla.ModelView):
    form_create_rules = [
        # Header and four fields. Email field will go above phone field.
        rules.FieldSet(('first_name', 'last_name', 'email', 'phone'), 'Personal'),
        # Separate header and few fields
        rules.Header('Address'),
        rules.Field('address'),
        # String is resolved to form field, so there's no need to explicitly use `rules.Field`
        'city',
        'zip',
        # Show macro from Flask-Admin lib.html (it is included with 'lib' prefix)
        rules.Container('rule_demo.wrap', rules.Field('notes'))
    ]

    # Use same rule set for edit page
    form_edit_rules = form_create_rules

    create_template = 'rule_create.html'
    edit_template = 'rule_edit.html'


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

# Create admin
admin = Admin(app, 'Simple Models')

# Add views
admin.add_view(FileView(File, db.session))
admin.add_view(ImageView(Image, db.session))
admin.add_view(RuleView(RuleSample, db.session, name='Rule'))

if __name__ == '__main__':

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
