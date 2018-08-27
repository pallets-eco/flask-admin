from flask import Flask, redirect, url_for
from flask_login import current_user, UserMixin, login_user, logout_user, LoginManager
from flask_admin.base import MenuLink, Admin, BaseView, expose


# Create fake user class for authentication
class User(UserMixin):
    users_id = 0

    def __init__(self, id=None):
        if not id:
            self.users_id += 1
            self.id = self.users_id
        else:
            self.id = id


# Create menu links classes with reloaded accessible
class AuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return not current_user.is_authenticated


# Create custom admin view for authenticated users
class MyAdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('authenticated-admin.html')

    def is_accessible(self):
        return current_user.is_authenticated


# Create flask app
app = Flask(__name__, template_folder='templates')

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


@app.route('/login/')
def login_view():
    login_user(User())
    return redirect(url_for('admin.index'))


@app.route('/logout/')
def logout_view():
    logout_user()
    return redirect(url_for('admin.index'))


login_manager = LoginManager()
login_manager.init_app(app)


# Create user loader function
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


if __name__ == '__main__':
    # Create admin interface
    admin = Admin(name='Example: Menu')
    admin.add_view(MyAdminView(name='Authenticated'))

    # Add home link by url
    admin.add_link(MenuLink(name='Back Home', url='/'))

    # Add login link by endpoint
    admin.add_link(NotAuthenticatedMenuLink(name='Login',
                                            endpoint='login_view'))

    # Add links with categories
    admin.add_link(MenuLink(name='Google', category='Links', url='http://www.google.com/'))
    admin.add_link(MenuLink(name='Mozilla', category='Links', url='http://mozilla.org/'))

    # Add logout link by endpoint
    admin.add_link(AuthenticatedMenuLink(name='Logout',
                                         endpoint='logout_view'))

    admin.init_app(app)

    # Start app
    app.run(debug=True)
