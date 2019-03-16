import os
import os.path as op
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin
from flask_admin.contrib.sqla import ModelView


# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(64))

    def __unicode__(self):
        return self.name


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(64))
    content = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name


# Customized admin interface
class CustomView(ModelView):
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'


class UserAdmin(CustomView):
    column_searchable_list = ('name',)
    column_filters = ('name', 'email')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create admin with custom base template
admin = admin.Admin(app, 'Example: Layout-BS3', base_template='layout.html', template_mode='bootstrap3')

# Add views
admin.add_view(UserAdmin(User, db.session))
admin.add_view(CustomView(Page, db.session))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    db.drop_all()
    db.create_all()

    first_names = [
        'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie','Sophie', 'Mia',
        'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
        'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
    ]
    last_names = [
        'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
        'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
        'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
    ]

    for i in range(len(first_names)):
        user = User()
        user.name = first_names[i] + " " + last_names[i]
        user.email = first_names[i].lower() + "@example.com"
        db.session.add(user)

    sample_text = [
        {
            'title': "de Finibus Bonorum et Malorum - Part I",
            'content': "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor \
                        incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud \
                        exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure \
                        dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
                        Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt \
                        mollit anim id est laborum."
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part II",
            'content': "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque \
                        laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto \
                        beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur \
                        aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi \
                        nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, \
                        adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam \
                        aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam \
                        corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum \
                        iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum \
                        qui dolorem eum fugiat quo voluptas nulla pariatur?"
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part III",
            'content': "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium \
                        voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati \
                        cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id \
                        est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam \
                        libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod \
                        maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. \
                        Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet \
                        ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur \
                        a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis \
                        doloribus asperiores repellat."
        }
    ]

    for entry in sample_text:
        page = Page()
        page.title = entry['title']
        page.content = entry['content']
        db.session.add(page)

    db.session.commit()
    return

if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True)
