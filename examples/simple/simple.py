from flask import Flask

from flask.ext import admin


# Create custom admin view
class MyAdminView(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('myadmin.html')


class AnotherAdminView(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('anotheradmin.html')

    @admin.expose('/test/')
    def test(self):
        return self.render('test.html')


# Create flask app
app = Flask(__name__, template_folder='templates')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin interface
    admin = admin.Admin()
    admin.add_view(MyAdminView(category='Test'))
    admin.add_view(AnotherAdminView(category='Test'))
    admin.init_app(app)

    # Start app
    app.debug = True
    app.run()
