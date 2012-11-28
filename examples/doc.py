from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456790'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_ECHO'] = True

# .. read settings
db = SQLAlchemy(app)


# .. model declarations here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(128))

if __name__ == '__main__':
    admin = Admin(app)
    admin.add_view(ModelView(User, db.session))

    db.create_all()
    app.run('0.0.0.0', 8000)
