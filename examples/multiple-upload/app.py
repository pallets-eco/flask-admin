# -*- coding: utf-8 -*-

import os
import os.path as op
import ast

from jinja2 import Markup

from sqlalchemy.event import listens_for

from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin, form
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import MultipleImageUploadField


# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config["SECRET_KEY"] = "1234567890"

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Create directory for file & image fields to use
file_path = op.join(op.dirname(__file__), "static/upload/files")
try:
    os.mkdir(file_path)
except OSError:
    pass

image_path = op.join(op.dirname(__file__), "static/upload/images")
try:
    os.mkdir(image_path)
except OSError:
    pass


# Create models
class ModelHasMultipleFileAndImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    files = db.Column(db.String(1024))
    images = db.Column(db.String(1024))


# Delete hooks for models, delete files if models are getting deleted
@listens_for(ModelHasMultipleFileAndImage, "after_delete")
def after_images(mapper, connection, target):
    if target.files:
        files = ast.literal_eval(target.files)
        for file in files:
            try:
                os.remove(op.join(file_path, file))
            except OSError:
                pass

    if target.images:
        images = ast.literal_eval(target.images)
        for image in images:
            try:
                os.remove(op.join(image_path, image))
            except OSError:
                pass

            try:
                os.remove(op.join(image_path, form.thumbgen_filename(image)))
            except OSError:
                pass


class ModelViewHasMultipleFileAndImage(ModelView):

    form_overrides = {
        'files': form.MultipleFileUploadField
    }

    form_args = {
        'files': {
            'label': 'Files',
            'base_path': file_path
        }
    }

    def _list_files(view, context, model, name):

        if not model.files:

            return ""

        return Markup("<br />".join("<a href='{}'>{}</a>"
                                    .format(url_for("static", filename="upload/files/" + filename), filename)
                                    for filename in ast.literal_eval(model.files)))

    def _list_thumbnail(view, context, model, name):

        if not model.images:
            return ""

        def gen_img(filename):
            return '<img src="{}">'.format(url_for('static', filename="upload/images/"
                                                                      + form.thumbgen_filename(filename)))

        return Markup("<br />".join([gen_img(image) for image in ast.literal_eval(model.images)]))

    column_formatters = {
        'files': _list_files,
        'images': _list_thumbnail
    }

    form_extra_fields = {
        "images": MultipleImageUploadField("Images",
                                           base_path=image_path,
                                           url_relative_path="upload/images/",
                                           thumbnail_size=(100, 100, True))
    }


# Flask views
@app.route('/')
def index():

    return "<a href='/admin/'>Click me to get to Admin!</a>"


@app.before_first_request
def build_sample_db():

    db.drop_all()
    db.create_all()

# Create admin
admin = Admin(app, "Example: Multiple Upload", template_mode="bootstrap3")

# Add views
admin.add_view(ModelViewHasMultipleFileAndImage(ModelHasMultipleFileAndImage, db.session))


if __name__ == "__main__":

    # Start app
    app.run(debug=True)
