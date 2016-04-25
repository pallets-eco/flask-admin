from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin
from flask_admin.contrib import sqla

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_db_3.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    pets = db.relationship('Pet', backref='person')

    def __unicode__(self):
        return self.name


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    available = db.Column(db.Boolean)

    def __unicode__(self):
        return self.name


class PersonAdmin(sqla.ModelView):
    """ Override ModelView to filter options available in forms. """

    def create_form(self):
        return self._use_filtered_parent(
            super(PersonAdmin, self).create_form()
        )

    def edit_form(self, obj):
        return self._use_filtered_parent(
            super(PersonAdmin, self).edit_form(obj)
        )

    def _use_filtered_parent(self, form):
        form.pets.query_factory = self._get_parent_list
        return form

    def _get_parent_list(self):
        # only show available pets in the form
        return Pet.query.filter_by(available=True).all()

    def __unicode__(self):
        return self.name


# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy - Filtered Form Selectable',
                    template_mode='bootstrap3')
admin.add_view(PersonAdmin(Person, db.session))
admin.add_view(sqla.ModelView(Pet, db.session))

if __name__ == '__main__':
    # Recreate DB
    db.drop_all()
    db.create_all()

    person = Person(name='Bill')
    pet1 = Pet(name='Dog', available=True)
    pet2 = Pet(name='Fish', available=True)
    pet3 = Pet(name='Ocelot', available=False)
    db.session.add_all([person, pet1, pet2, pet3])
    db.session.commit()

    # Start app
    app.run(debug=True)
