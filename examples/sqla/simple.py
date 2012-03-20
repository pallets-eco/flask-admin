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


# Create models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    # Required for administrative interface
    def __unicode__(self):
        return self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User, backref='posts')

    def __unicode__(self):
        return self.title


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Customized Post model admin
class PostAdmin(sqlamodel.ModelView):
    # Visible columns in the list view
    list_columns = ('title', 'user')

    # List of columns that can be sorted. For 'user' column, use User.username as
    # a column.
    sortable_columns = ('title', ('user', User.username))

    # Rename 'title' columns to 'Post Title' in list view
    rename_columns = dict(title='Post Title')

    # Pass arguments to WTForms. In this case, change label for text field to
    # be 'Big Text' and add required() validator.
    form_args = dict(
                    text=dict(label='Big Text', validators=[wtf.required()])
                )

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(PostAdmin, self).__init__(Post, session)

if __name__ == '__main__':
    # Create admin
    admin = adminex.Admin('Simple Models')

    # Add views
    admin.add_view(sqlamodel.ModelView(User, db.session))
    admin.add_view(PostAdmin(db.session))

    # Associate with an app
    admin.apply(app)

    # Create DB
    db.create_all()

    # Start app
    app.debug = True
    app.run()
