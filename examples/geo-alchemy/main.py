from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.geoa import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql+psycopg2://flask_admin_geo:flask_admin_geo@localhost/flask_admin_geo"
)
app.config["SQLALCHEMY_ECHO"] = True
# Credentials for loading map tiles from Mapbox
app.config["FLASK_ADMIN_MAPS"] = True
app.config["FLASK_ADMIN_MAPS_SEARCH"] = False
app.config["FLASK_ADMIN_MAPBOX_MAP_ID"] = "light-v10"
app.config["FLASK_ADMIN_MAPBOX_ACCESS_TOKEN"] = "..."
# When creating new shapes, use this default map center
app.config["FLASK_ADMIN_DEFAULT_CENTER_LAT"] = -33.918861
app.config["FLASK_ADMIN_DEFAULT_CENTER_LONG"] = 18.423300
# If you want to use Google Maps, set the API key here
app.config["FLASK_ADMIN_GOOGLE_MAPS_API_KEY"] = "..."
db = SQLAlchemy(app)
admin = Admin(app, name="Example: GeoAlchemy", theme=Bootstrap4Theme())


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


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


class LeafletModelView(ModelView):
    edit_modal = True


class OSMModelView(ModelView):
    tile_layer_url = "{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    tile_layer_attribution = (
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        "contributors"
    )


if __name__ == "__main__":
    admin.add_view(LeafletModelView(Point, db.session, category="Points"))
    admin.add_view(OSMModelView(MultiPoint, db.session, category="Points"))
    admin.add_view(LeafletModelView(Polygon, db.session, category="Polygons"))
    admin.add_view(OSMModelView(MultiPolygon, db.session, category="Polygons"))
    admin.add_view(LeafletModelView(LineString, db.session, category="Lines"))
    admin.add_view(OSMModelView(MultiLineString, db.session, category="Lines"))

    with app.app_context():
        db.create_all()

    app.run(debug=True)
