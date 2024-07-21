import os
import os.path as op

from werkzeug.utils import secure_filename
from sqlalchemy import event

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

from wtforms import fields

import flask_admin as admin
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.form import RenderTemplateWidget
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib.sqla.fields import InlineModelFormList

# Create application
app = Flask(__name__)

# Create dummy secret key so we can use sessions
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


class ImageType(db.Model):
    """
    Just so the LocationImage can have another foreign key,
    so we can test the "form_ajax_refs" inside the "inline_models"
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self) -> str:
        """
        Represent this model as a string
        (e.g. in the Image Type list dropdown when creating an inline model)
        """
        return self.name


class LocationImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alt = db.Column(db.Unicode(128))
    path = db.Column(db.String(64))

    location_id = db.Column(db.Integer, db.ForeignKey(Location.id))
    location = db.relation(Location, backref='images')

    image_type_id = db.Column(db.Integer, db.ForeignKey(ImageType.id))
    image_type = db.relation(ImageType, backref='images')


# Register after_delete handler which will delete image file after model gets deleted
@event.listens_for(Location, 'after_delete')
def _handle_image_delete(mapper, conn, target):
    for location_image in target.images:
        try:
            if location_image.path:
                os.remove(op.join(base_path, location_image.path))
        except:
            pass


# This widget uses custom template for inline field list
class CustomInlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(CustomInlineFieldListWidget, self).__init__('field_list.html')


# This InlineModelFormList will use our custom widget and hide row controls
class CustomInlineModelFormList(InlineModelFormList):
    widget = CustomInlineFieldListWidget()

    def display_row_controls(self, field):
        return False


# Create custom InlineModelConverter and tell it to use our InlineModelFormList
class CustomInlineModelConverter(InlineModelConverter):
    inline_field_list_type = CustomInlineModelFormList


# Customized inline form handler
class LocationImageInlineModelForm(InlineFormAdmin):
    form_excluded_columns = ('path',)

    form_label = 'Image'

    # Setup AJAX lazy-loading for the ImageType inside the inline model
    form_ajax_refs = {
        "image_type": QueryAjaxModelLoader(
            name="image_type",
            session=db.session,
            model=ImageType,
            fields=("name",),
            order_by="name",
            placeholder="Please use an AJAX query to select an image type for the image",
            minimum_input_length=0,
        )
    }

    def __init__(self):
        super(LocationImageInlineModelForm, self).__init__(LocationImage)

    def postprocess_form(self, form_class):
        form_class.upload = fields.FileField('Image')
        return form_class

    def on_model_change(self, form, model, is_created):
        file_data = request.files.get(form.upload.name)

        if file_data:
            model.path = secure_filename(file_data.filename)
            file_data.save(op.join(base_path, model.path))


# Administrative class
class LocationAdmin(ModelView):
    inline_model_form_converter = CustomInlineModelConverter

    inline_models = (LocationImageInlineModelForm(),)

    def __init__(self):
        super().__init__(Location, db.session, name='Locations')


# Simple page to show images
@app.route('/')
def index():
    locations = db.session.query(Location).all()
    return render_template('locations.html', locations=locations)


def first_time_setup():
    """Run this to setup the database for the first time"""
    with app.app_context():
        # Create DB
        db.drop_all()
        db.create_all()

        # Add some image types for the form_ajax_refs inside the inline_model
        image_types = ("JPEG", "PNG", "GIF")
        for image_type in image_types:
            model = ImageType(name=image_type)
            db.session.add(model)

        db.session.commit()


if __name__ == '__main__':
    # Create upload directory
    try:
        os.mkdir(base_path)
    except OSError:
        pass

    # Create DB
    first_time_setup()

    # Create admin
    admin = admin.Admin(app, name='Example: Inline Models')
    admin.add_view(LocationAdmin())

    # Start app
    app.run(debug=True)
