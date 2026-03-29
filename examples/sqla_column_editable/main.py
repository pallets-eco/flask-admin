import enum
from datetime import date
from datetime import datetime
from datetime import time

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Cuisine(db.Model):
    __tablename__ = "cuisines"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __str__(self) -> str:
        return self.name


class SpiceLevel(enum.Enum):
    mild = "Mild"
    medium = "Medium"
    hot = "Hot"
    extra_hot = "Extra Hot"


class Dish(db.Model):
    __tablename__ = "dishes"
    id = db.Column(db.Integer, primary_key=True)
    # StringField
    name = db.Column(db.String(100), nullable=False)
    # TextAreaField
    description = db.Column(db.Text, nullable=True)
    # IntegerField
    calories = db.Column(db.Integer, nullable=True)
    # FloatField
    price = db.Column(db.Float, nullable=False)
    # BooleanField
    vegetarian = db.Column(db.Boolean, default=False)
    available = db.Column(db.Boolean, default=True)
    # DateField
    added_on = db.Column(db.Date, nullable=True)
    # TimeField
    available_from = db.Column(db.Time, nullable=True)
    # DateTimeField
    last_ordered = db.Column(db.DateTime, nullable=True)
    # Enum → SelectField
    spice_level = db.Column(db.Enum(SpiceLevel), nullable=True)
    # ForeignKey → QuerySelectField
    cuisine_id = db.Column(db.Integer, db.ForeignKey("cuisines.id"), nullable=True)
    cuisine = db.relationship("Cuisine", backref="dishes")

    def __str__(self) -> str:
        return self.name


class DishView(ModelView):
    column_list = [
        "id",
        "name",
        "description",
        "price",
        "calories",
        "vegetarian",
        "available",
        "spice_level",
        "cuisine",
        "added_on",
        "available_from",
        "last_ordered",
    ]
    column_editable_list = [
        "name",  # StringField
        "description",  # TextAreaField
        "price",  # FloatField
        "calories",  # IntegerField
        "vegetarian",  # BooleanField
        "available",  # BooleanField
        "spice_level",  # SelectField (enum)
        "cuisine",  # QuerySelectField (relation)
        "added_on",  # DateField
        "available_from",  # TimeField
        "last_ordered",  # DateTimeField
    ]
    column_labels = {
        "added_on": "Added On",
        "available_from": "Available From",
        "last_ordered": "Last Ordered",
        "spice_level": "Spice Level",
    }


class CuisineView(ModelView):
    column_editable_list = ["name"]


app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

Babel(app)
db.init_app(app)

admin = Admin(app, name="Kitchen Sink", theme=Bootstrap4Theme())
admin.add_view(DishView(Dish, db.session, name="Dishes"))
admin.add_view(CuisineView(Cuisine, db.session, name="Cuisines"))


with app.app_context():
    db.create_all()
    if not db.session.query(Dish).first():
        cuisines = [
            Cuisine(name="Italian"),
            Cuisine(name="Japanese"),
            Cuisine(name="Mexican"),
            Cuisine(name="Indian"),
            Cuisine(name="Thai"),
        ]
        db.session.add_all(cuisines)
        db.session.flush()

        dishes = [
            Dish(
                name="Margherita Pizza",
                description="Classic pizza with tomato, mozzarella, and basil",
                price=12.99,
                calories=850,
                vegetarian=True,
                available=True,
                spice_level=SpiceLevel.mild,
                cuisine=cuisines[0],
                added_on=date(2025, 1, 15),
                available_from=time(11, 0),
                last_ordered=datetime(2026, 3, 28, 19, 30),
            ),
            Dish(
                name="Tonkotsu Ramen",
                description="Rich pork bone broth with chashu and soft-boiled egg",
                price=15.50,
                calories=720,
                vegetarian=False,
                available=True,
                spice_level=SpiceLevel.medium,
                cuisine=cuisines[1],
                added_on=date(2025, 3, 20),
                available_from=time(11, 30),
                last_ordered=datetime(2026, 3, 29, 12, 15),
            ),
        ]
        db.session.add_all(dishes)
        db.session.commit()
        print("Seeded 5 cuisines and 6 dishes.")


if __name__ == "__main__":
    print("Visit http://127.0.0.1:5000/admin/dish/")
    print("Click any editable column value to edit inline.")
    app.run(debug=True)
