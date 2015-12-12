from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_admin.contrib import sqla
from flask_admin import Admin

# required for creating custom filters
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create model
class User(db.Model):
    def __init__(self, first_name, last_name, username, email):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    # Required for admin interface. For python 3 please use __str__ instead.
    def __unicode__(self):
        return self.username


# Create custom filter class
class FilterLastNameBrown(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(self.column == "Brown")
        else:
            return query.filter(self.column != "Brown")

    def operation(self):
        return 'is Brown'


# Add custom filter and standard FilterEqual to ModelView
class UserAdmin(sqla.ModelView):
    # each filter in the list is a filter operation (equals, not equals, etc)
    # filters with the same name will appear as operations under the same filter
    column_filters = [
        FilterEqual(column=User.last_name, name='Last Name'),
        FilterLastNameBrown(column=User.last_name, name='Last Name',
                            options=(('1', 'Yes'), ('0', 'No')))
    ]


admin = Admin(app, template_mode="bootstrap3")
admin.add_view(UserAdmin(User, db.session))


def build_sample_db():
    db.drop_all()
    db.create_all()
    user_obj1 = User("Paul", "Brown", "pbrown", "paul@gmail.com")
    user_obj2 = User("Luke", "Brown", "lbrown", "luke@gmail.com")
    user_obj3 = User("Serge", "Koval", "skoval", "serge@gmail.com")

    db.session.add_all([user_obj1, user_obj2, user_obj3])
    db.session.commit()


if __name__ == '__main__':
    build_sample_db()
    app.run(port=5000, debug=True)
