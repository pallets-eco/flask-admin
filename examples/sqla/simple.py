from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

from flask.ext import adminex, wtf
from flask.ext.adminex.ext import sqlamodel

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Create model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __unicode__(self):
        return self.username

    def __repr__(self):
        return '<User %r>' % self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User, backref='posts')


# Flask routes
@app.route('/')
def index():
    db.session.query(Post).join(User).order_by(User.username).all()

    return '<a href="/admin/">Click me to get to Admin!</a>'


class PostAdmin(sqlamodel.ModelView):
    list_columns = ('title', 'user')

    sortable_columns = ('title', ('user', User.username))
    rename_columns = dict(title='Tiiitle')

    form_args = dict(
                    text=dict(label='Big Text', validators=[wtf.required()])
                )

    def __init__(self, session):
        super(PostAdmin, self).__init__(Post, session)

if __name__ == '__main__':
    # Create admin
    admin = adminex.Admin('Simple Models')
    admin.add_view(sqlamodel.ModelView(User, db.session))
    admin.add_view(PostAdmin(db.session))
    admin.apply(app)

    # Create DB
    db.create_all()

    # Start app
    app.debug = True
    app.run('0.0.0.0')
