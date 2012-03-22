from flask import Flask, render_template

from flask.ext import adminex


# Create custom admin view
class MyAdminView(adminex.BaseView):
    @adminex.expose('/')
    def index(self):
        return self.render('myadmin.html')


class AnotherAdminView(adminex.BaseView):
    @adminex.expose('/')
    def index(self):
        return self.render('anotheradmin.html')

    @adminex.expose('/test/')
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
    admin = adminex.Admin(app)
    admin.add_view(MyAdminView(category='Test'))
    admin.add_view(AnotherAdminView(category='Test'))

    # Start app
    app.debug = True
    app.run()
