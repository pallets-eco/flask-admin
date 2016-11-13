from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

import flask_admin as admin
from flask_admin.contrib import sqla

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db_2.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class Screen(db.Model):
    __tablename__ = 'screen'
    id = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)

    @hybrid_property
    def number_of_pixels(self):
        return self.width * self.height


class ScreenAdmin(sqla.ModelView):
    """ Flask-admin can not automatically find a hybrid_property yet. You will
        need to manually define the column in list_view/filters/sorting/etc."""
    column_list = ['id', 'width', 'height', 'number_of_pixels']
    column_sortable_list = ['id', 'width', 'height', 'number_of_pixels']

    # Flask-admin can automatically detect the relevant filters for hybrid properties.
    column_filters = ('number_of_pixels', )


# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy2', template_mode='bootstrap3')
admin.add_view(ScreenAdmin(Screen, db.session))

if __name__ == '__main__':

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
