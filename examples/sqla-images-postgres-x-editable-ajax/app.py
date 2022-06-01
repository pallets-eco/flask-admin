import base64
from pathlib import Path
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

import flask_admin as admin
from flask_admin.form import RenderTemplateWidget
from flask_admin.form.upload import ImageUploadFieldDB
from flask_admin.model.fields import ColorField
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib.sqla.fields import InlineModelFormList

# Create application
app = Flask(__name__)

# Create dummy secret key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add filter function to jinja2 environment
def b64encode(binary):
    """Read the image into Pillow and convert to a string for the browser"""
    image = ImageUploadFieldDB.binary_to_image(binary)
    image_bytes = ImageUploadFieldDB.image_to_bytes(image, format=image.format)
    data_uri = base64.b64encode(image_bytes).decode("utf-8")
    return data_uri

app.jinja_env.filters['b64encode'] = b64encode

db = SQLAlchemy(app)


# Create models

# many-to-many relationship between User and Image classes/tables
user_image_rel = db.Table(
    "user_image_rel",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "image_id",
        db.Integer,
        db.ForeignKey("images.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(db.Model):
    """Locations table, for which we may have images"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    favorite_color = db.Column(db.String(6))

    images = relationship("Image", secondary=user_image_rel, back_populates="users")

    
class Location(db.Model):
    """Locations table, for which we may have images"""
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))

    images = relationship("Image", back_populates="location")


class Image(db.Model):
    """
    Create a table into which we can upload images
    """
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

    # Many-to-one relationship with locations table
    location_id = db.Column(db.Integer, db.ForeignKey(Location.id))
    location = relationship("Location", back_populates="images")

    # Many-to-many relationship with users table
    users = relationship("User", secondary=user_image_rel, back_populates="images")



class CustomInlineFieldListWidget(RenderTemplateWidget):
    """This widget uses custom template for inline field list"""
    def __init__(self):
        super(CustomInlineFieldListWidget, self).__init__('field_list.html')


class CustomInlineModelFormList(InlineModelFormList):
    """This InlineModelFormList will use our custom widget and hide row controls"""
    widget = CustomInlineFieldListWidget()

    def display_row_controls(self, field):
        return False


class CustomInlineModelConverter(InlineModelConverter):
    """Create custom InlineModelConverter and tell it to use our InlineModelFormList"""
    inline_field_list_type = CustomInlineModelFormList


class InlineModelForm(InlineFormAdmin):
    """Customized inline form handler"""

    form_label = 'Image'

    form_extra_fields = {
        "image": ImageUploadFieldDB("Image")
    }

    def __init__(self):
        return super(InlineModelForm, self).__init__(Image)


class LocationAdmin(ModelView):
    """Administrative class for viewing location records"""
    can_view_details = True

    inline_model_form_converter = CustomInlineModelConverter

    inline_models = (InlineModelForm(),)

    def __init__(self):
        super(LocationAdmin, self).__init__(Location, db.session, name='Locations')


class UserAdmin(ModelView):
    """Administrative class for viewing location-image records"""

    # Demonstrate many-to-many relationship between users and images,
    # with x-editable select-multiple dropdown.
    # Also demonstrate the x-editable color-picker.
    column_editable_list = ["images", "favorite_color"]

    # For displaying a thumbnail in the list view
    column_formatters = {"images": ImageUploadFieldDB.display_thumbnail}
    
    # Use AJAX with x-editable in the list view, to speed up list view display
    form_ajax_refs = {
        "images": QueryAjaxModelLoader(
            "images",
            db.session,
            Image,
            fields=["name"],
            order_by="name",
            placeholder="Please select an image",
        ),
    }

    # The color field is an Input(type="color") field
    form_overrides = {
        "favorite_color": ColorField,
    }

    def __init__(self):
        super(UserAdmin, self).__init__(User, db.session, name='Users')


class ImageAdmin(ModelView):
    """Administrative class for viewing location-image records"""
    
    # Location is x-editable in the list view
    column_editable_list = ["location"]

    # For displaying a thumbnail
    column_formatters = {"image": ImageUploadFieldDB.display_thumbnail}

    # This field uploads large binary data directly to a database, instead of to a file
    form_extra_fields = {
        "image": ImageUploadFieldDB("Image")
    }
    
    # Location is x-editable in the list view, and still we can use AJAX
    form_ajax_refs = {
        "location": QueryAjaxModelLoader(
            "location",
            db.session,
            Location,
            fields=["name"],
            order_by="name",
            placeholder="Please select a location",
            **{
                "minimum_input_length": 0,
            },
        ),
    }

    def __init__(self):
        super(ImageAdmin, self).__init__(Image, db.session, name='Images')


@app.route('/')
def index():
    """Simple page to show images"""
    images = db.session.query(Image).all()
    thumbnails = [
        ImageUploadFieldDB.display_thumbnail(None, None, image, "image")
        for image in images
    ]
    return render_template('locations.html', thumbnails=thumbnails)


def first_time_setup():
    """Run this to setup the database for the first time"""
    # Create DB
    db.drop_all()
    db.create_all()

    # Upload the test image to the database
    test_image = Path(__file__).parent.joinpath("static").joinpath("test_image.jpg")
    with open(test_image, "rb") as file:
        image_data = file.read()
    image = ImageUploadFieldDB.binary_to_image(image_data)
    image_bytes = ImageUploadFieldDB.image_to_bytes(image, image.format)
    image = Image(name="test image", image=image_bytes)
    db.session.add(image)

    # Upload a test location, with image
    location = Location(name="first location", images=[image])
    db.session.add(location)

    # Upload a test user, with image and favorite color
    user = User(name="Test User", favorite_color="#007BFF", images=[image])
    db.session.add(user)

    db.session.commit()

    return


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, name='Example: Images in Database', template_mode="bootstrap4")

    # Add views
    admin.add_view(UserAdmin())
    admin.add_view(LocationAdmin())
    admin.add_view(ImageAdmin())

    # Setup the database
    first_time_setup()

    # Start app
    app.run(debug=True)
