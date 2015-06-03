from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin
from geoalchemy2.types import Geometry
from flask_admin.contrib.geoa import ModelView


# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://flask_admin_geo:flask_admin_geo@localhost/flask_admin_geo'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.config['MAPBOX_MAP_ID'] = '...'
app.config['MAPBOX_ACCESS_TOKEN'] = '...'


class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("POINT"))


class MultiPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("MULTIPOINT"))


class Polygon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("POLYGON"))


class MultiPolygon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("MULTIPOLYGON"))


class LineString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("LINESTRING"))


class MultiLineString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    point = db.Column(Geometry("MULTILINESTRING"))


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

# Create admin
admin = admin.Admin(app, name='Example: GeoAlchemy')

# Add views
admin.add_view(ModelView(Point, db.session, category='Points'))
admin.add_view(ModelView(MultiPoint, db.session, category='Points'))
admin.add_view(ModelView(Polygon, db.session, category='Polygons'))
admin.add_view(ModelView(MultiPolygon, db.session, category='Polygons'))
admin.add_view(ModelView(LineString, db.session, category='Lines'))
admin.add_view(ModelView(MultiLineString, db.session, category='Lines'))

if __name__ == '__main__':

    db.create_all()

    # Start app
    app.run(debug=True)
