import flask_admin as admin
from flask import Flask
from flask_admin.contrib.geoa import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry

# Create application
app = Flask(__name__)
app.config.from_pyfile("config.py")
db = SQLAlchemy(app)


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
@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create admin
admin = admin.Admin(app, name="Example: GeoAlchemy", theme=Bootstrap4Theme())


class LeafletModelView(ModelView):
    edit_modal = True


class OSMModelView(ModelView):
    tile_layer_url = "{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    tile_layer_attribution = (
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        "contributors"
    )


# Add views
admin.add_view(LeafletModelView(Point, db.session, category="Points"))
admin.add_view(OSMModelView(MultiPoint, db.session, category="Points"))
admin.add_view(LeafletModelView(Polygon, db.session, category="Polygons"))
admin.add_view(OSMModelView(MultiPolygon, db.session, category="Polygons"))
admin.add_view(LeafletModelView(LineString, db.session, category="Lines"))
admin.add_view(OSMModelView(MultiLineString, db.session, category="Lines"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # Start app
    app.run(debug=True)
