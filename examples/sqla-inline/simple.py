import os
import os.path as op

from werkzeug import secure_filename
from sqlalchemy import event

from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy

from wtforms import fields

from flask.ext import admin
from flask.ext.admin.form import RenderTemplateWidget
from flask.ext.admin.model.form import InlineFormAdmin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.form import InlineModelConverter
from flask.ext.admin.contrib.sqla.fields import InlineModelFormList

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Figure out base upload path
base_path = op.join(op.dirname(__file__), 'static')


# Create models
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))


class LocationImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alt = db.Column(db.Unicode(128))
    path = db.Column(db.String(64))

    location_id = db.Column(db.Integer, db.ForeignKey(Location.id))
    location = db.relation(Location, backref='images')


# Register after_delete handler which will delete image file after model gets deleted
@event.listens_for(LocationImage, 'after_delete')
def _handle_image_delete(mapper, conn, target):
    try:
        if target.path:
            os.remove(op.join(base_path, target.path))
    except:
        pass


# This widget uses custom template for inline field list
class CustomInlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(CustomInlineFieldListWidget, self).__init__('field_list.html')


# This InlineModelFormList will use our custom widget
class CustomInlineModelFormList(InlineModelFormList):
    widget = CustomInlineFieldListWidget()


# Create custom InlineModelConverter and tell it to use our InlineModelFormList
class CustomInlineModelConverter(InlineModelConverter):
    inline_field_list_type = CustomInlineModelFormList


# Customized inline form handler
class InlineModelForm(InlineFormAdmin):
    form_excluded_columns = ('path',)

    form_label = 'Image'

    def __init__(self):
        return super(InlineModelForm, self).__init__(LocationImage)

    def postprocess_form(self, form_class):
        form_class.upload = fields.FileField('Image')
        return form_class

    def on_model_change(self, form, model):
        file_data = request.files.get(form.upload.name)

        if file_data:
            model.path = secure_filename(file_data.filename)
            file_data.save(op.join(base_path, model.path))


# Administrative class
class LocationAdmin(ModelView):
    inline_model_form_converter = CustomInlineModelConverter

    inline_models = (InlineModelForm(),)

    def __init__(self):
        super(LocationAdmin, self).__init__(Location, db.session, name='Locations')


# Simple page to show images
@app.route('/')
def index():
    locations = db.session.query(Location).all()
    return render_template('locations.html', locations=locations)


if __name__ == '__main__':
    # Create upload directory
    try:
        os.mkdir(base_path)
    except OSError:
        pass

    # Create admin
    admin = admin.Admin(app, 'Inline Fun')

    # Add views
    admin.add_view(LocationAdmin())

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
